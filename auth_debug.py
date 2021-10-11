import os
import json

if __name__ == '__main__':
    print('Checking envs:')
    path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    print('GOOGLE_APPLICATION_CREDENTIALS:', path)

    print('File content:')
    with open(path, 'r') as f:
        lines = [line for line in f.readlines()]
        print('Lines in the file:', len(lines))
        for item in lines:
            if 'private_key' in item:
                print('. . .')
            else:
                print(item)

    with open(path, 'r') as f:
        json_content = json.load(f)

    print('Everything loaded fine.')

    raise Exception('Stop building container!')
