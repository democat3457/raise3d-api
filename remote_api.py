from dotenv import load_dotenv
load_dotenv()

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

    response = json.loads(requests.get(f'{API}/login', params={'sign': signature, 'timestamp': stamp}).text)
    if response['status'] == 0:
        print('Error while logging in:', json.dumps(response, indent=2))
        quit(1)

    token = response['data']['token']

def main():
    global token

    login()

    print('[get|post] [/apiendpoint] [param1 param2 param3 ...]')
    print('param format:')
    print(' * key=value for query param')
    print(' * key:value for body param')

    while True:
        s = input('::: ')
        if s == 'exit' or s == 'quit':
            print('Exiting...')
            break

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
            kwargs['params'].update(map(lambda x: tuple(x.split('=', 1)), query_params))
        if len(body_params):
            kwargs['data'] = dict(map(lambda x: tuple(x.split(':', 1)), body_params))

        print(api_url, kwargs)

        if type == 'get':
            response = json.loads(requests.get(api_url, **kwargs).text)
        elif type == 'post':
            response = json.loads(requests.post(api_url, **kwargs).text)
        else:
            print(f'Invalid type {type}: expected get or post')
            continue

        if response['status'] == 1:
            if 'data' in response:
                print(json.dumps(response['data'], indent=2))
            else:
                print('Success!')
        else:
            print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()
