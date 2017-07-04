import json
import time
import os
import requests
import sys

# ========================================================
# 0. Argment Parser
# ========================================================
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--ini', default="", help='setting.ini file path')
args = parser.parse_args()

setting_file_path = args.ini

param_dir, setting_file = setting_file_path.rsplit("/", 1)

# ========================================================
# 1. Load Setting
# ========================================================
import configparser

config = configparser.ConfigParser()
config.read(args.ini)
section1 = 'development'
name = config.get(section1, 'name')  # localhost

# ========================================================
# 2. Load Model
# ========================================================


# ========================================================
# 3. Pre Process
# ========================================================
LOG_FILE_PATH = os.path.join(param_dir, "log.txt")


def logger_reset():
    with open(LOG_FILE_PATH, "w") as fp:
        fp.write("")


def logger(msg: str):
    print(msg)
    with open(LOG_FILE_PATH, "a") as fp:
        fp.write(msg + "\n")


# ========================================================
# 4. Define Callback
# ========================================================
def alive_callback(values: dict):
    sorted(values.items(), key=lambda x: x[0])
    rv = requests.post("http://localhost:5000/api/{}".format(values["name"]), json=values)
    logger("POST Alive : {} {}".format(values, rv.status_code))


def error_finish_callback(err_msg: str):
    logger("POST Error Finish : {}, {}".format(name, err_msg))


def finish_callback(values: dict):
    sorted(values.items(), key=lambda x: x[0])
    rv = requests.post("http://localhost:5000/api/{}".format(values["name"]), json=values)
    logger("POST Finish : {} {}".format(values, rv.status_code))


# ========================================================
# ========================================================
if __name__ == '__main__':

    # 5. Start Calculation
    logger("====================")

    try:
        for i in range(3):
            time.sleep(1)
            alive_callback({"name": name, "epoch": i+1, "accuracy": i * i, "loss": i + 1})
    except Exception as e:
        logger(str(e))

    finish_callback({"name": name, "elapsed": 123})

