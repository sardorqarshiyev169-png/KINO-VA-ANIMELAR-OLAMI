import sqlite3

def clean_animes():
    conn = sqlite3.connect('data/movies.sqlite3')
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()
    cur.execute("DELETE FROM contents WHERE content_type='anime'")
    count = cur.rowcount
    conn.commit()
    conn.close()
    print(f"Successfully deleted {count} animes.")

if __name__ == "__main__":
    clean_animes()
