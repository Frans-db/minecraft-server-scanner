import sqlite3

db = sqlite3.connect('db.db')
c = db.cursor()
c.execute('SELECT * FROM ips WHERE scanned == 0')
rows = c.fetchall()
print(len(rows))
# c.execute('UPDATE ips SET scanned = 0')
# db.commit()