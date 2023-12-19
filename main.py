"""
Subscribe to a single message source, emit alarm signal till acknowledged.
"""

import json
import subprocess
import time
import traceback

from typing import Literal
import requests
from inputimeout import TimeoutOccurred, inputimeout

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
    """
    Set volume as value by key

    Args:
        key(str): volume key to set
        value(int): volume value to set
    """
    cmd = [TERMUX_VOLUME, key, str(value)]
    print("running:", cmd)
    subprocess.run(cmd, check=False)


def set_volume(setting: dict[str, int]):
    """
    Set volumes by setting

    Args:
        setting(dict): pairs of volume key and value
    """
    for k, v in setting.items():
        set_single_volume(k, v)


def get_volume_setting():
    """
    Getting a list of volume settings

    Returns:
        data(list):
            each item is a dict
            structure: 'volume' (int), 'max_volume' (int), 'stream' (str)
    """
    result = subprocess.run(
        [TERMUX_VOLUME], capture_output=True, encoding=ENCODING, check=True
    )
    data = json.loads(result.stdout)
    return data


def set_by_key(vollist: list, key: Literal["max_volume", "volume"]):
    """Construct and set volume settings

    Args:
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
        key(Literal["max_volume", "volume"]): volume key to get value from"""
    setting = {elem[STREAM]: elem[key] for elem in vollist}
    set_volume(setting)


def set_by_maxvol(vollist: list):
    """Construct and set volume settings by max volume

    Args:
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
    """
    set_by_key(vollist, MAX_VOLUME)


def set_by_volume(vollist: list):
    """Construct and set volume settings by volume

    Args:
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
    """
    set_by_key(vollist, VOLUME)


def emit_alarm_signal(msg: str, alarm_filepath: str):
    """Emit alarm by vibration, playing alarm sound and reading message
    
    Args:
        msg(str): message to handle
        alarm_filepath(str): alarm filepath
    """
    subprocess.run([TERMUX_VIBRATE, "-d", str(VIBRATION_MILISECONDS), "-f"], check=True)
    subprocess.run([PLAY, alarm_filepath], check=True)
    print("received message:", msg)
    subprocess.run([ESPEAK, msg], check=True)


def msg_acknowledged_loop(msg: str, alarm_filepath: str):
    """Repeatedly emitting alarm signal till acknowledged
    
    Args:
        msg(str): message to handle
        alarm_filepath(str): alarm filepath
    """
    while True:
        emit_alarm_signal(msg, alarm_filepath)
        try:
            ans = inputimeout(prompt=ACKNOWLEDGE_PROMPT, timeout=ACKNOWLEDGE_TIMEOUT)
            if ans == YES:
                break
        except KeyboardInterrupt:
            print("interrupted")
        except TimeoutOccurred:
            print("timeout occured")


def handle_msg_with_vol_control(msg: str, vollist: list, alarm_filepath: str):
    """Get current volume settings, set volume to maximum value, emit alarm event, finally recover volume settings
    
    Args:
        msg(str): message to handle
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
        alarm_filepath(str): alarm filepath
    """
    try:
        vollist = get_volume_setting()
        set_by_maxvol(vollist)
        msg_acknowledged_loop(msg, alarm_filepath)
    finally:
        set_by_volume(vollist)


def decode_line_and_get_msg(line: bytes):
    """Decode line, load as json dictionary and get message by key 'message'
    
    Args:
        line(bytes): line to decode

    Returns:
        msg(str|None): message by key 'message'
    """
    data = json.loads(line)
    msg = data.get(MESSAGE, None)
    return msg


def read_stream_and_handle_msg(
    sess: requests.Session, url: str, vollist: list, alarm_filepath: str
):
    """
    Setup connection stream and read message per line
    Emit alarm if message is not empty

    Args:
        sess(requests.Session): request session object
        url(str): message subscription url
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
        alarm_filepath(str): alarm filepath
    """
    stream = sess.get(url, stream=True)
    for line in stream.iter_lines():
        msg = decode_line_and_get_msg(line)
        if msg:
            handle_msg_with_vol_control(msg, vollist, alarm_filepath)


def recover_from_exception():
    """Print exception traceback and sleep for preconfigured recovery time"""
    traceback.print_exc()
    print(f"recovering from exception ({RECOVERY_SLEEP_TIME} secs)")
    time.sleep(RECOVERY_SLEEP_TIME)


def read_stream_loop(
    sess: requests.Session, url: str, vollist: list, alarm_filepath: str
):
    """Indefinitely reading message stream from server till keyboard interrupt

    Args:
        sess(requests.Session): request session object
        url(str): message subscription url
        vollist(list): list of volume configuration obtained by `get_volume_setting()`
        alarm_filepath(str): alarm filepath
    """
    while True:
        try:
            read_stream_and_handle_msg(sess, url, vollist, alarm_filepath)
        except KeyboardInterrupt:
            print("exiting because of keyboard interrupt")
            break
        except:
            recover_from_exception()


def print_settings(url: str, alarm_filepath: str):
    """Print settings for main loop

    Args:
        url(str): message subscription url
        alarm_filepath(str): alarm filepath
    """
    print(f"listen on: {url}")
    print(f"alarm filepath: {alarm_filepath}")


def main_loop(url: str, alarm_filepath: str):
    """
    Get volume settings and start reading message streams
    Restore volume settings on exit

    Args:
        url(str): message subscription url
        alarm_filepath(str): alarm filepath
    """
    print_settings(url, alarm_filepath)
    vollist = get_volume_setting()
    sess = requests.Session()
    try:
        read_stream_loop(sess, url, vollist, alarm_filepath)
    finally:
        set_by_volume(vollist)


if __name__ == "__main__":
    main_loop(
        url="http://ntfy.sh/crysis_or_panic/json",
        alarm_filepath="mixkit-classic-short-alarm-993.wav",
    )
