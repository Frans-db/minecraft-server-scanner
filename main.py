import masscan
import time
import os
from twisted.internet import reactor
from quarry.net.client import ClientFactory, ClientProtocol
import sqlite3
import json
import argparse

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


class PingProtocol(ClientProtocol):
    def status_response(self, data):
        ip = self.transport.getPeer().host
        copied_data = {}

        for k, v in sorted(data.items()):
            if k != "favicon":
                print('%s --> %s' % (k, v))
                copied_data[k] = v

        with open(f'./data/servers/{ip}.json', 'w+') as f:
            json.dump(copied_data, f)

        reactor.stop()


class PingFactory(ClientFactory):
    protocol = PingProtocol
    protocol_mode_next = 'status'


def load_ip_ranges(filename: str):
    with open(filename) as f:
        return f.readlines()


def scan_ips():
    ips = load_ip_ranges('./data/ip_ranges/hetzner.txt')
    for i, ip_range in enumerate(ips):
        print(f'[{i:2}/{len(ips)}]: Range: {ip_range}')
        if os.path.isfile(f'./data/scans/result_{i}.txt'):
            continue
        ip_range_results = []
        try:
            mas = masscan.PortScanner()
            mas.scan(ip_range, ports='25565', arguments='--max-rate 1000')
            for ip in mas._scan_result['scan']:
                host_data = mas._scan_result['scan'][ip][0]
                if host_data['proto'] == 'tcp' and host_data['status'] == 'open':
                    ip_range_results.append(ip)
        except Exception as e:
            print('Exception thrown')
            print(e)
            time.sleep(30)

        string_result = '\n'.join(ip_range_results)
        with open(f'./data/scans/result_{i}.txt', 'w+') as f:
            f.write(string_result)
        insert_file_into_database(f'result_{i}.txt')


def insert_files_into_database():
    files = os.listdir('./data/scans/')
    for filename in files:
        insert_file_into_database(filename)


def insert_file_into_database(filename: str):
    with open(f'./data/scans/{filename}') as f:
        ips = f.readlines()
        ips = [(ip.strip(),) for ip in ips]
    try:
        db.cursor().executemany('INSERT INTO ips (ip) VALUES (?)', ips)
    except sqlite3.IntegrityError:
        print(f'Filename {filename} already imported')
    db.commit()


def check_for_minecraft_server():
    c = db.cursor()
    c.execute('SELECT ip FROM ips WHERE scanned == 0')
    ip = c.fetchone()[0]
    c.execute('UPDATE ips SET scanned = 1 WHERE ip = ?', (ip, ))
    db.commit()

    factory = PingFactory()
    factory.connect(ip, 25565)
    reactor.run()


def print_minecraft_servers():
    files = os.listdir('./data/servers')
    for filename in files:
        with open(f'./data/servers/{filename}') as f:
            data = json.load(f)
        ip = {filename[:-5]}
        description = data['description']
        if 'text' in data['description']:
            description = data['description']['text']
        if 'extra' in data['description']:
            for extra in data['description']['extra']:
                description += extra['text']
                
            
        print(f'[{ip}] - {description}')
    print(f'Saved {len(files)} servers')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    args = parser.parse_args()

    if args.mode == 'scan':
        scan_ips()
    elif args.mode == 'check_server':
        check_for_minecraft_server()
    elif args.mode == 'print':
        print_minecraft_servers()
    elif args.mode == 'create':
        create_tables()
    elif args.mode == 'drop':
        drop_tables()


if __name__ == '__main__':
    main()
