import sqlite3

def get_user(conn, username: str):
    query = "SELECT id FROM users WHERE username = '" + username + "';"
    cur = conn.execute(query)
    return cur.fetchone()

if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
    conn.execute("INSERT INTO users (username) VALUES ('alice')")
    print(get_user(conn, "alice"))
