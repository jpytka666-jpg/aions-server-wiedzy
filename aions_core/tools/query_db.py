import sqlite3
import os

def query_db():
    db_path = r"D:\AIONS-INTEGRATION\aions_scan.db"
    if not os.path.exists(db_path):
        print("DB not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find which folder has the most JSON chunks
        query = """
        SELECT parent_path, COUNT(*) as count 
        FROM files 
        WHERE extension = '.json' AND path LIKE '%chunks%'
        GROUP BY parent_path 
        ORDER BY count DESC 
        LIMIT 10;
        """
        
        results = cursor.execute(query).fetchall()
        for row in results:
            print(f"Count: {row[1]} | Path: {row[0]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    query_db()
