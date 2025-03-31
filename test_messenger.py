# test_messenger.py
import os
import unittest
import sqlite3
from node import init_db, log_message, DB_FILE

# helped by chatgpt for the testing

class TestMessenger(unittest.TestCase):
    def setUp(self):
        # Use a test-specific DB
        self.test_db = "test_messages.db"
        global DB_FILE
        DB_FILE = self.test_db
        init_db()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_init_db_creates_table(self):
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        table = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table)

    def test_log_message_inserts_data(self):
        log_message("2025-03-30T12:00:00", "me", "peer", "Hello")
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages")
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], "peer")  # Receiver

if __name__ == '__main__':
    unittest.main()
