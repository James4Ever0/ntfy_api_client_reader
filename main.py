import requests
import subprocess
import time
import json
from inputimeout import inputimeout

TERMUX_VOLUME = 'termux-volume'

def set_volume(setting):
    for k,v in setting.items():
        cmd=[TERMUX_VOLUME, k, str(v)]
        print('running:', cmd)
        subprocess.run(cmd)

def get_volume_setting():
    result=subprocess.run([TERMUX_VOLUME], capture_output=True, encoding='utf-8')
    data=json.loads(result.stdout)
    return data


def set_by_maxvol(vollist):
    setting={elem['stream']:elem['max_volume'] for elem in vollist}
    set_volume(setting)

def set_by_volume(vollist):
    setting={elem['stream']:elem['volume'] for elem in vollist}
    set_volume(setting)

vollist=get_volume_setting()

url = 'http://ntfy.sh/crysis_or_panic/json'
alarm = 'mixkit-classic-short-alarm-993.wav'
sess=requests.Session()

stream=sess.get(url, stream=True)

try:
    for line in stream.iter_lines():
        line=line.decode('utf-8')
        data=json.loads(line)
        msg=data.get('message', None)
        if msg:
            try:
                vollist=get_volume_setting()
                set_by_maxvol(vollist)
                while True:
                    subprocess.run(['termux-vibrate', '-d','2000','-f'])
                    subprocess.run(['play', alarm])
                    print('received message:', msg)
                    subprocess.run(['espeak',msg])
                    try:
                        ans=inputimeout(prompt="acknowledged? (y/n) ", timeout=3)
                        if ans == 'y':
                            break
                    except:
                        pass
            finally:       
                set_by_volume(vollist)
finally:
    set_by_volume(vollist)
