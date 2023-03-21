import sqlite3
import json

file = './data/out.json'
with open(file) as f:
    data = json.load(f)

ips = [(row['ip'],) for row in data]
db = sqlite3.connect('db.db')
c = db.cursor()
for ip in ips:
    try:
        c.execute('INSERT INTO ips (ip) VALUES (?)', ip)
    except sqlite3.IntegrityError:
        print(ip)
db.commit()