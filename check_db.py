import sqlite3

conn = sqlite3.connect("output/warehouse.db")

print("AUDIT TABLE COLUMNS:")

columns = conn.execute(
    "PRAGMA table_info(pipeline_audit)"
).fetchall()

for column in columns:
    print(column[1])

print("\nLATEST AUDIT RECORDS:")

rows = conn.execute(
    "SELECT * FROM pipeline_audit ORDER BY rowid DESC LIMIT 5"
).fetchall()

for row in rows:
    print(row)

conn.close()