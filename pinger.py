import threading
import masscan
import time
import os
from twisted.internet import reactor
from quarry.net.client import ClientFactory, ClientProtocol
import sqlite3
import json
import multiprocessing

db = sqlite3.connect("db.db")


def create_tables():
    db.cursor().execute("""
    CREATE TABLE ips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT UNIQUE,
        scanned INTEGER DEFAULT 0
    )
    """)


def drop_tables():
    db.cursor().execute('DROP TABLE ips')


def status(ip):
    class PingProtocol(ClientProtocol):
        def status_response(self, data):
            ip = self.transport.getPeer().host

            for k, v in sorted(data.items()):
                if k != "favicon":
                    print('%s --> %s' % (k, v))

            with open(f'./data/servers/{ip}.json', 'w+') as f:
                json.dump(data, f)

            


    class PingFactory(ClientFactory):
        protocol = PingProtocol
        protocol_mode_next = 'status'

    factory = PingFactory()
    factory.connect(ip, 25565)

def load_ip_ranges(filename: str):
    with open(filename) as f:
        return f.readlines()



def check_for_minecraft_server():
    num_threads = 500
    c = db.cursor()
    c.execute('SELECT ip FROM ips WHERE scanned == 0')
    rows = c.fetchmany(num_threads)
    c.executemany('UPDATE ips SET scanned = 1 WHERE ip = ?', rows)
    db.commit()
    ips = [row[0] for row in rows]
    threads = []
    for ip in ips:
        reactor.callInThread(status, ip)
    reactor.run()
    
if __name__ == '__main__':
    p = multiprocessing.Process(target=check_for_minecraft_server)
    p.start()
    time.sleep(30)
    p.terminate()
    p.join()

