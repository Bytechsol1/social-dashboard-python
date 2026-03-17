import sqlite3
import os
from api.database import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
metrics = conn.execute("SELECT * FROM metrics").fetchall()

print("All Metrics:")
for m in metrics:
    print(f"[{m['date']}] {m['source']} {m['metric_name']}: {m['value']}")

conn.close()
