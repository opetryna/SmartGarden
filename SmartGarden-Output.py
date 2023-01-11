#!/usr/bin/python3

import json
import sys

import RPi.GPIO as GPIO


with open("/etc/SmartGarden/config.json", "r") as f:
    config = json.load(f)["Output"]

pin = None
state = None
if len(sys.argv) >= 2:
    pin = config[sys.argv[1]]["pin"]
else:
    raise Exception("Output name not provided!")
if len(sys.argv) == 3:
    state = int(sys.argv[2])

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

if state is not None:
    GPIO.output(pin, state)

print(GPIO.input(pin), end="")
