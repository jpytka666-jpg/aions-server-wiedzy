import sqlite3

def check_schema():
    db_path = r"D:\AIONS-INTEGRATION\aions_scan.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        t_name = table[0]
        print(f"\nSchema for {t_name}:")
        cursor.execute(f"PRAGMA table_info({t_name})")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  {col[1]} ({col[2]})")
            
    conn.close()

if __name__ == "__main__":
    check_schema()
