import requests
import subprocess
import time
import json
from inputimeout import inputimeout, TimeoutOccurred
import traceback

# binary executables
TERMUX_VOLUME = "termux-volume"
TERMUX_VIBRATE = "termux-vibrate"
PLAY = "play"
ESPEAK = "espeak"

# dict keys
STREAM = "stream"
MAX_VOLUME = "max_volume"
VOLUME = "volume"
MESSAGE = "message"

# io settings
ENCODING = "utf-8"

# numbers
RECOVERY_SLEEP_TIME = 3
ACKNOWLEDGE_TIMEOUT = 3
VIBRATION_MILISECONDS = 2000

# interaction
YES = "y"
ACKNOWLEDGE_PROMPT = "acknowledged? (y/n) "

def set_single_volume(key: str, value: int):
    cmd = [TERMUX_VOLUME, key, str(value)]
    print("running:", cmd)
    subprocess.run(cmd)


def set_volume(setting):
    for k, v in setting.items():
        set_single_volume(k, v)


def get_volume_setting():
    result = subprocess.run([TERMUX_VOLUME], capture_output=True, encoding=ENCODING)
    data = json.loads(result.stdout)
    return data


def set_by_key(vollist: list, key: str):
    setting = {elem[STREAM]: elem[key] for elem in vollist}
    set_volume(setting)


def set_by_maxvol(vollist: list):
    set_by_key(vollist, MAX_VOLUME)


def set_by_volume(vollist: list):
    set_by_key(vollist, VOLUME)


def emit_alarm_signal(msg: str, alarm_filepath: str):
    subprocess.run([TERMUX_VIBRATE, "-d", str(VIBRATION_MILISECONDS), "-f"])
    subprocess.run([PLAY, alarm_filepath])
    print("received message:", msg)
    subprocess.run([ESPEAK, msg])


def msg_acknowledged_loop(msg: str, alarm_filepath: str):
    while True:
        emit_alarm_signal(msg, alarm_filepath)
        try:
            ans = inputimeout(
                prompt=ACKNOWLEDGE_PROMPT, timeout=ACKNOWLEDGE_TIMEOUT
            )
            if ans == YES:
                break
        except KeyboardInterrupt:
            print("interrupted")
        except TimeoutOccurred:
            print("timeout occured")


def handle_msg_with_vol_control(msg: str, vollist: list, alarm_filepath: str):
    try:
        vollist = get_volume_setting()
        set_by_maxvol(vollist)
        msg_acknowledged_loop(msg, alarm_filepath)
    finally:
        set_by_volume(vollist)


def decode_line_and_get_msg(line: bytes):
    data = json.loads(line)
    msg = data.get(MESSAGE, None)
    return msg


def read_stream_and_handle_msg(
    sess: requests.Session, url: str, vollist: list, alarm_filepath: str
):
    stream = sess.get(url, stream=True)
    for line in stream.iter_lines():
        msg = decode_line_and_get_msg(line)
        if msg:
            handle_msg_with_vol_control(msg, vollist, alarm_filepath)


def recover_from_exception():
    traceback.print_exc()
    print(f"recovering from exception ({RECOVERY_SLEEP_TIME} secs)")
    time.sleep(RECOVERY_SLEEP_TIME)


def read_stream_loop(
    sess: requests.Session, url: str, vollist: list, alarm_filepath: str
):
    while True:
        try:
            read_stream_and_handle_msg(sess, url, vollist, alarm_filepath)
        except KeyboardInterrupt:
            print("exiting because of keyboard interrupt")
            break
        except:
            recover_from_exception()


def print_settings(url: str, alarm_filepath: str):
    print(f"listen on: {url}")
    print(f"alarm filepath: {alarm_filepath}")


def main_loop(url: str, alarm_filepath: str):
    print_settings(url, alarm_filepath)
    vollist = get_volume_setting()
    sess = requests.Session()
    try:
        read_stream_loop(sess, url, vollist, alarm_filepath)
    finally:
        set_by_volume(vollist)


if __name__ == "__main__":
    url = "http://ntfy.sh/crysis_or_panic/json"
    alarm_filepath = "mixkit-classic-short-alarm-993.wav"
    main_loop(url, alarm_filepath)
