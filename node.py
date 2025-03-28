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

# === Socket Handlers ===

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

def handle_send(conn, send_queue):
    while True:
        if not send_queue:
            time.sleep(0.1)
            continue

        message, msg_time = send_queue.pop(0)
        if message.lower() == "exit":
            conn.close()
            break

        try:
            conn.settimeout(10.0)
            conn.sendall(message.encode())
            print("Message sent.")
            log_message(datetime.fromtimestamp(msg_time).isoformat(), "me", "peer", message)
        except socket.timeout:
            print("Failed to send message: timeout.")
        except Exception as e:
            print(f"Failed to send message: {e}")

        conn.settimeout(None)

# === Connection Setup ===

def instantiate_socket(my_port, result_container):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, my_port))
        s.listen()
        print(f"[Server] Listening on {HOST}:{my_port}...")
        conn, addr = s.accept()
        print(f"[Server] Connected by {addr}")
        result_container.append(conn)

def connect_to_peer(peer_port, result_container):
    while True:
        try:
            peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_sock.connect((HOST, peer_port))
            print(f"[Client] Connected to peer at {HOST}:{peer_port}")
            result_container.append(peer_sock)
            break
        except ConnectionRefusedError:
            time.sleep(1)
        except Exception as e:
            print(f"[Client] Connection failed: {e}")
            time.sleep(1)

# === Main App ===

def main():
    init_db()

    my_port = int(input("Enter the port you want to receive messages on: "))
    peer_port = int(input("Enter the port you want to communicate with: "))

    server_conn = []
    client_conn = []

    server_thread = threading.Thread(target=instantiate_socket, args=(my_port, server_conn))
    client_thread = threading.Thread(target=connect_to_peer, args=(peer_port, client_conn))

    server_thread.start()
    client_thread.start()

    server_thread.join()
    client_thread.join()

    recv_thread = threading.Thread(target=handle_receive, args=(server_conn[0],), daemon=True)
    recv_thread.start()

    send_queue = []
    send_thread = threading.Thread(target=handle_send, args=(client_conn[0], send_queue), daemon=True)
    send_thread.start()

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
