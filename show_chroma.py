import sqlite3

db_path = r"E:\server wiedzy\data\chroma\chroma.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Pokaż tabele
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("=" * 50)
print("TABELE W CHROMADB:")
print("=" * 50)
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"  {t}: {count} rekordów")

print("\n" + "=" * 50)
print("PRZYKŁADOWE DANE Z 'collections':")
print("=" * 50)
cursor.execute("SELECT * FROM collections LIMIT 5")
for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 50)
print("PRZYKŁADOWE DANE Z 'embeddings' (pierwsze 3):")
print("=" * 50)
cursor.execute("SELECT id, collection_id FROM embeddings LIMIT 3")
for row in cursor.fetchall():
    print(row)

conn.close()
print("\n✅ Gotowe!")
