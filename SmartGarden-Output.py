#!/usr/bin/python3

import json
import sys

import RPi.GPIO as GPIO


class Output:

    def __init__(self, config):
        self.config = config
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
    
    def read_output(self, channel: str) -> int:
        pin = self.config[channel]["pin"]
        GPIO.setup(pin, GPIO.OUT)
        return GPIO.input(pin)

    def write_output(self, channel: str, state: int) -> None:
        pin = self.config[channel]["pin"]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, state)


def main():
    with open("/etc/SmartGarden/config.json", "r") as f:
        config = json.load(f)["Output"]
    output = Output(config)

    channels = None
    state = None
    if len(sys.argv) >= 2:
        channels = [sys.argv[1]] if sys.argv[1] != '*' else list(config.keys())
    else:
        raise Exception("Output name not provided!")
    if len(sys.argv) == 3:
        state = int(sys.argv[2])

    if state is not None:
        for channel in channels:
            output.write_output(channel, state)

    results = []
    for channel in channels:
        results.append(str(output.read_output(channel)))
    print(" ".join(results), end="")


if __name__ == "__main__":
    main()
