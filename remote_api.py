from dotenv import load_dotenv
load_dotenv()

import argparse
import json
import os
import requests
from hashlib import md5, sha1
from datetime import datetime

PRINTER_IP = os.getenv("RAISE3D_PRINTER_IP")
PRINTER_PORT = os.getenv("RAISE3D_PRINTER_PORT")
API = f'http://{PRINTER_IP}:{PRINTER_PORT}/v1'

API_PASSWORD = os.getenv('RAISE3D_API_PASSWORD')

token = ''

def login():
    global token

    stamp = int(datetime.now().timestamp() * 1000)
    signature = md5(sha1(f"password={API_PASSWORD}&timestamp={stamp}".encode('utf-8')).hexdigest().encode('utf-8')).hexdigest()

    response = requests.get(f'{API}/login', params={'sign': signature, 'timestamp': stamp}).json()
    if response['status'] == 0:
        print('Error while logging in:', json.dumps(response, indent=2))
        quit(1)

    token = response['data']['token']

def format_param(param: str, delimiter:str='='):
    parts = param.split(delimiter, 1)
    key, value = parts[0], parts[1]
    try:
        value = int(value)
    except ValueError:
        try:
            value = float(value)
        except ValueError:
            value = str(value)
    return (key, value)

def main(verbose: bool = False):
    global token

    def printv(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    login()

    print('[get|post] [/apiendpoint] [param1 param2 param3 ...]')
    print('param format:')
    print(' * key=value for query param')
    print(' * key:value for body param')

    while True:
        s = input('::: ')
        if s in ('exit', 'quit'):
            print('Exiting...')
            break
        if s in ('login', 'relog', 'relogin'):
            login()
            print('Relogged and refreshed token.')
            continue

        type, endpoint_params = s.split(' ', 1)
        if ' ' in endpoint_params:
            endpoint, params = endpoint_params.split(' ', 1)
        else:
            endpoint, params = endpoint_params, ''

        api_url = f'{API}{endpoint}'

        params = params.split(' ')

        query_params = list(filter(lambda x: '=' in x, params))
        body_params = list(filter(lambda x: ':' in x, params))
        kwargs = { 'params': {'token': token} }

        if len(query_params):
            kwargs['params'].update(map(lambda x: format_param(x, '='), query_params))
        if len(body_params):
            kwargs['json'] = dict(map(lambda x: format_param(x, ':'), body_params))

        printv('URL:   ', api_url)
        printv('kwargs:', kwargs)

        if type == 'get':
            response = requests.get(api_url, **kwargs)
        elif type == 'post':
            response = requests.post(api_url, **kwargs)
        else:
            print(f'Invalid type {type}: expected get or post')
            continue

        if not len(response.text):
            if response.status_code == 400:
                print('Invalid or missing parameters')
                continue
            obj = {
                "error": {
                    "code": response.status_code
                },
                "status": 0,
            }
        else:
            obj = response.json()

        if obj['status'] == 1:
            if 'data' in obj:
                print(json.dumps(obj['data'], indent=2))
            else:
                print('Success!')
        else:
            print(json.dumps(obj, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    main(args.verbose)
