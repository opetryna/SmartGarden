#!/usr/bin/python3

import json
import sys

import RPi.GPIO as GPIO


with open("/etc/SmartGarden/config.json", "r") as f:
    config = json.load(f)["Watering"]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config["pin"], GPIO.OUT)

state = None
if len(sys.argv) == 2:
    state = int(sys.argv[1])

if state is not None:
    GPIO.output(config["pin"], state)

print(GPIO.input(config["pin"]), end="")
