import socket
import threading
import time
import sqlite3
from datetime import datetime

HOST = "127.0.0.1"
DB_FILE = "messages.db"

# === Database Setup ===

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sender TEXT,
            receiver TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_message(timestamp, sender, receiver, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (timestamp, sender, receiver, content)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, sender, receiver, content))
    conn.commit()
    conn.close()

# Socket threads

def handle_receive(conn):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("Peer disconnected.")
                break
            message = data.decode()
            timestamp = datetime.now().isoformat()
            print(f"\nPeer: {message}")
            log_message(timestamp, "peer", "me", message)
        except:
            break

def handle_send(send_queue, conn_container):
    while True:
        if not send_queue:
            time.sleep(1)
            continue

        message, msg_time = send_queue[0]

        if message.lower() == "exit":
            if conn_container and conn_container[0]:
                conn_container[0].close()
            break

        try:
            if conn_container and conn_container[0]:
                conn = conn_container[0]
                conn.settimeout(10.0)
                conn.sendall(message.encode())
                print("Message sent.")
                log_message(datetime.fromtimestamp(msg_time).isoformat(), "me", "peer", message)
                send_queue.pop(0)  # Remove message after successful send
            else:
                print("Waiting for peer to connect...")
        except (socket.timeout, BrokenPipeError, ConnectionResetError):
            print("Failed to send message: peer unavailable. Retrying in 1 minute...")
            if conn_container:
                conn_container[0] = None
        except Exception as e:
            print(f"Send error: {e}")
        finally:
            if conn_container and conn_container[0]:
                conn_container[0].settimeout(None)

        time.sleep(60)

# Connection functions

def instantiate_socket(my_port, server_conn):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, my_port))
        s.listen()
        print(f"[Server] Listening on {HOST}:{my_port}...")
        conn, addr = s.accept()
        print(f"[Server] Connected by {addr}")
        server_conn.append(conn)

def maintain_client_connection(peer_port, conn_container):
    while True:
        if conn_container and conn_container[0]:
            time.sleep(1)
            continue

        try:
            peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_sock.connect((HOST, peer_port))
            print(f"[Client] Connected to peer at {HOST}:{peer_port}")
            conn_container.clear()
            conn_container.append(peer_sock)
        except ConnectionRefusedError:
            time.sleep(1)
        except Exception as e:
            print(f"[Client] Connection attempt failed: {e}")
            time.sleep(1)

# Messaging loop

def main():
    init_db()

    my_port = int(input("Enter the port you want to receive messages on: "))
    peer_port = int(input("Enter the port you want to communicate with: "))

    server_conn = []
    client_conn = []

    # Start server and client connection threads
    threading.Thread(target=instantiate_socket, args=(my_port, server_conn), daemon=True).start()
    threading.Thread(target=maintain_client_connection, args=(peer_port, client_conn), daemon=True).start()
    while not server_conn:
        time.sleep(0.5)

    # Start receiving messages from peer
    recv_thread = threading.Thread(target=handle_receive, args=(server_conn[0],), daemon=True)
    recv_thread.start()

    send_queue = []
    send_thread = threading.Thread(target=handle_send, args=(send_queue, client_conn), daemon=True)
    send_thread.start()

    # Main input loop
    while True:
        decision = input("Log off (Y/N)? ").strip().upper()
        if decision == 'Y':
            send_queue.append(("exit", time.time()))
            break
        elif decision == 'N':
            message = input("Enter a message: ")
            send_queue.append((message, time.time()))
        else:
            print("Please enter Y or N")

    send_thread.join()

if __name__ == "__main__":
    main()
