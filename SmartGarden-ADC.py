#!/usr/bin/python3

import json

import serial


class Conversions:

    @staticmethod
    def luminosity(value: int) -> float:
        return value * (100/1024)

    @staticmethod
    def moisture(value: int) -> float:
        return value * (100/1024)


with open("/etc/SmartGarden/config.json", "r") as f:
    config = json.load(f)["ADC"]

s = serial.Serial(config["device"], config["baud"], timeout=1)
s.reset_input_buffer()

def write_value(channel, value):
    parameter = config["inputs"][channel]
    if parameter == None:
        return

    transform = getattr(Conversions, parameter)
    value = transform(int(value))
    
    with open(f"/var/SmartGarden/{parameter}", "w") as f:
        f.write(f"{value:.1f}")

while True:
    if s.in_waiting > 0:
        values = s.readline().decode().strip().split("\t")
        if len(values) == 6:
            print(values)
            for channel, value in enumerate(values):
                write_value(channel, value)
