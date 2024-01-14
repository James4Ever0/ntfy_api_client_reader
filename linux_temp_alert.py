import json
import subprocess
import time
import rich
import tempfile

ENCODING = "utf-8"
SCAN_INTERVAL = 10
ALERT_CONFIRMATION_THRESHOLD = 3
TEMP_THRESHOLD = 75  # celsius
RESP_THRESHOLD = 100


def jsonWalk(jsonObj, location=[]):
    # this is not tuple. better convert it first?
    # mlocation = copy.deepcopy(location)
    if type(jsonObj) == dict:
        for key in jsonObj:
            content = jsonObj[key]
            if type(content) not in [dict, list, tuple]:
                yield location + [key], content
            else:
                # you really ok with this?
                for mkey, mcontent in jsonWalk(content, location + [key]):
                    yield mkey, mcontent
    elif type(jsonObj) in [list, tuple]:
        for key, content in enumerate(jsonObj):
            # content = jsonObj[key]
            if type(content) not in [dict, list, tuple]:
                yield location + [key], content
            else:
                for mkey, mcontent in jsonWalk(content, location + [key]):
                    yield mkey, mcontent
    else:
        raise Exception("Not a JSON compatible object: {}".format(type(jsonObj)))


def measure_system_responsiveness():
    metrics = {}

    # Measure command execution speed
    start_time_cmd = time.time()
    subprocess.run(["echo", "hello"], capture_output=True, encoding="utf-8", check=True)
    end_time_cmd = time.time()
    exec_time_cmd = end_time_cmd - start_time_cmd
    exec_per_second_cmd = 1 / exec_time_cmd
    metrics["command_execution_speed"] = exec_per_second_cmd

    # Measure file I/O speed
    start_time_file = time.time()
    with tempfile.TemporaryFile("w+") as f:
        f.write("test")
    end_time_file = time.time()
    file_io_time = end_time_file - start_time_file
    metrics["file_io_speed"] = 1 / file_io_time

    # Measure network I/O speed (example using ping)
    start_time_net = time.time()
    _ = subprocess.run(["ping", "-c", "5", "baidu.com"], capture_output=True, text=True)
    end_time_net = time.time()
    net_io_time = end_time_net - start_time_net
    metrics["network_io_speed"] = 5 / net_io_time  # Assuming 5 pings

    # Measure arithmetic calculation speed (example using Fibonacci)
    start_time_fib = time.time()
    _ = fibonacci(30)  # Calculate the 30th Fibonacci number
    end_time_fib = time.time()
    fib_time = end_time_fib - start_time_fib
    metrics["arithmetic_speed"] = 1 / fib_time  # Results in calculation per second

    # Measure loop execution speed
    start_time_loop = time.time()
    loop_count = 10000
    i = 0
    for _ in range(loop_count):  # Perform a simple loop a large number of times
        i+=1
    end_time_loop = time.time()
    loop_time = end_time_loop - start_time_loop
    metrics["loop_speed"] = 1 / loop_time  # Loop iterations per second

    return metrics


def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


def get_sensor_data():
    result = subprocess.run(
        ["sensors", "-j"], capture_output=True, encoding=ENCODING, check=True
    )
    data = json.loads(result.stdout)
    return data


past_data = {}


while True:
    data = get_sensor_data()
    metrics = measure_system_responsiveness()
    # {
    # 'command_execution_speed': 506.5584541062802,
    # 'file_io_speed': 5440.083009079118,
    # 'network_io_speed': 1.2365655592571214,
    # 'arithmetic_speed': 3.5074622247606877,
    # 'loop_speed': 2030.1568247821879
    # }
    for klist, v in jsonWalk(data):
        last_key = klist[-1]
        if last_key.startswith("temp") and last_key.endswith("_input"):
            rich.print(klist, v)
    rich.print("responsiveness:", metrics)
    time.sleep(SCAN_INTERVAL)
