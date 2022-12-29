#!/usr/bin/python3

import json
import time
import board
import adafruit_dht


with open("/etc/SmartGarden/config.json", "r") as f:
    config = json.load(f)["DHT"]

device = getattr(adafruit_dht, config["model"])
pin = getattr(board, config["pin"])
sensor = device(pin)

def write_value(parameter, value):
    with open(f"/var/SmartGarden/{parameter}", "w") as f:
        f.write(f"{value:.1f}")

while True:
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        
        print(f"Temperature: {temperature:.1f} C / Humidity: {humidity:.1f} %")
        write_value("temperature", temperature)
        write_value("humidity", humidity)
    
    # It is not unusual for a reading to fail.
    except RuntimeError as e:
        print(e.args[0])
    
    except Exception as e:
        sensor.exit()
        raise e

    # DHT should not be read more than once every two seconds.
    time.sleep(max(2, config["interval"]))
