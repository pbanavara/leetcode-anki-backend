import sqlite3


def init_database():
    conn = sqlite3.connect("leetcode_training.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS problems
                (id INTEGER PRIMARY KEY,
                 title TEXT,
                 description TEXT,
                 difficulty TEXT,
                 acceptance_rate REAL,
                 frequency REAL,
                 related_topics TEXT,
                 asked_by_faang BOOLEAN)""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_attempts
                (id INTEGER PRIMARY KEY,
                 user_id TEXT NOT NULL,
                 problem_id INTEGER,
                 iterations INTEGER,
                 user_difficulty TEXT,
                 leetcode_difficulty TEXT,
                 timestamp TIMESTAMP,
                 FOREIGN KEY(problem_id) REFERENCES problems(id))""")

    conn.commit()
    conn.close()
