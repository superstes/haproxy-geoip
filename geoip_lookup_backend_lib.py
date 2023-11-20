#!/usr/bin/python3

# requirements: pip install maxminddb

from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from maxminddb import open_database

PORT = 6970

# https://ipinfo.io/account/data-downloads
DATABASES = {
    'country': {'file': '/tmp/country.mmdb', 'attr': 'country', 'fallback': '00'},
    'continent': {'file': '/tmp/country.mmdb', 'attr': 'continent', 'fallback': '00'},
    'asn': {'file': '/tmp/asn.mmdb', 'attr': 'asn', 'fallback': '0'},
    'asname': {'file': '/tmp/asn.mmdb', 'attr': 'name', 'fallback': '-'},
}


def _lookup_mmdb(db: dict, ip: str) -> str:
    try:
        if not Path(db['file']).is_file():
            return db['fallback']

        with open_database(db['file']) as db_reader:
            return db_reader.get(ip)[db['attr']]

    except (RuntimeError, KeyError):
        return db['fallback']


def _ensure_str(data: (str, list)) -> str:
    if isinstance(data, list):
        if len(data) > 0:
            return data[0]

        return ''

    return data


class WebRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)

        if 'lookup' not in q or _ensure_str(q['lookup']) not in DATABASES:
            self.send_response(400)
            self.end_headers()
            self.wfile.write('Got unsupported lookup'.encode('utf-8'))

        if 'ip' not in q:
            self.send_response(400)
            self.end_headers()
            self.wfile.write('No IP provided'.encode('utf-8'))

        lookup = _ensure_str(q['lookup'])
        ip = _ensure_str(q['ip'])
        data = _lookup_mmdb(DATABASES[lookup], ip)
        print(f"{lookup} | {ip} => {data}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), WebRequestHandler)
    server.serve_forever()
