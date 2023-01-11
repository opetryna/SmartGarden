#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from threading import Thread
import time
import json
import subprocess


def _update_params(old, new):
    for key in old.keys():
        if key in new:
            old[key] = new[key]


class SmartGardenSensors:

    def __init__(self):
        pass

    def get_temperature(self):
        path = "/var/SmartGarden/temperature"
        data = {"units": "C"}

        data["timestamp"] = int(os.path.getmtime(path))
        with open(path, "r") as f:
            data["value"] = float(f.read())
        
        return "temperature", data
    
    def get_humidity(self):
        path = "/var/SmartGarden/humidity"
        data = {"units": "%"}

        data["timestamp"] = int(os.path.getmtime(path))
        with open(path, "r") as f:
            data["value"] = float(f.read())
        
        return "humidity", data

    def get_moisture(self):
        path = "/var/SmartGarden/moisture"
        data = {"units": "%"}

        data["timestamp"] = int(os.path.getmtime(path))
        with open(path, "r") as f:
            data["value"] = float(f.read())

        return "moisture", data
    
    def get_luminosity(self):
        path = "/var/SmartGarden/luminosity"
        data = {"units": "%"}

        data["timestamp"] = int(os.path.getmtime(path))
        with open(path, "r") as f:
            data["value"] = float(f.read())
        
        return "luminosity", data


class SmartGardenActuators:

    def __init__(self):
        pass

    def get_watering(self):
        path = "/usr/local/bin/SmartGarden-Output"
        
        output = int(subprocess.check_output([path, "watering"]))
        state = bool(output)

        return "watering", {"enabled": state}

    def set_watering(self, params):
        path = "/usr/local/bin/SmartGarden-Output"

        state = str(int(params["enabled"]))
        subprocess.check_output([path, "watering", state])

        return self.get_watering()


class SmartGardenController(Thread):

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.settings = {
            "enabled": False
        }
        _update_params(self.settings, config["settings"])

    def get(self):
        return "controller", self.settings

    def set(self, params):
        _update_params(self.settings, params)
        return self.get()
    
    def run(self):
        while True:
            if self.settings["enabled"]:
                
                pass

            time.sleep(self.config["interval"])


class SmartGardenHTTPRequestHandler(BaseHTTPRequestHandler):

    def respond(self, code, results=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if results:
            output = json.dumps({k: v for k, v in results}, indent=2) + "\n"
            self.wfile.write(output.encode())

    def respond_error(self, code, message):
        results = [(
            "error", {
                "status": code,
                "message": message
            }
        )]
        self.respond(code, results)

    @property
    def json(self):
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)
        params = json.loads(data)
        return params

    def do_GET(self):
        try:
            results = []

            path = self.path.strip("/")
            if path == "":
                self.respond(204)

            elif path == "sensors":
                results.append(sensors.get_temperature())
                results.append(sensors.get_humidity())
                results.append(sensors.get_moisture())
                results.append(sensors.get_luminosity())
            elif path == "sensors/temperature":
                results.append(sensors.get_temperature())
            elif path == "sensors/humidity":
                results.append(sensors.get_humidity())
            elif path == "sensors/moisture":
                results.append(sensors.get_moisture())
            elif path == "sensors/luminosity":
                results.append(sensors.get_luminosity())
            
            elif path == "actuators":
                results.append(actuators.get_watering())
            elif path == "actuators/watering":
                results.append(actuators.get_watering())
            
            elif path == "controller":
                results.append(controller.get())

            else:
                self.respond_error(404, "Not Found")
            
            if results:
                self.respond(200, results)
        
        except Exception as e:
            self.respond_error(500, e.args[0])

    def do_PATCH(self):
        try:
            results = []

            path = self.path.strip("/")
            if path == "":
                self.respond_error(405, "Method Not Allowed")
            
            elif path.startswith("sensors"):
                self.respond_error(405, "Method Not Allowed")
            
            elif path == "actuators":
                self.respond_error(405, "Method Not Allowed")
            elif path == "actuators/watering":
                if not controller.settings["enabled"]:
                    results.append(actuators.set_watering(self.json))
                else:
                    self.respond_error(403, "Cannot set actuators while the controller is enabled.")
            
            elif path == "controller":
                results.append(controller.set(self.json))

            else:
                self.respond_error(404, "Not Found")
            
            if results:
                self.respond(200, results)
        
        except Exception as e:
            self.respond_error(500, e.args[0])


def main():
    with open("/etc/SmartGarden/config.json", "r") as f:
        config = json.load(f)
    
    global sensors, actuators, controller
    sensors = SmartGardenSensors()
    actuators = SmartGardenActuators()
    controller = SmartGardenController(config["Controller"])
    controller.start()

    httpd = HTTPServer((config["API"]["bind_ip"], config["API"]["bind_port"]), SmartGardenHTTPRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
