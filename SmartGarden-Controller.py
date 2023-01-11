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

    def read_output(self, channel: str) -> bool:
        path = "/usr/local/bin/SmartGarden-Output"

        output = int(subprocess.check_output([path, channel]))
        value = bool(output)
        
        return value

    def write_output(self, channel: str, value: bool) -> None:
        path = "/usr/local/bin/SmartGarden-Output"

        value = str(int(value))
        subprocess.check_output([path, channel, value])

        return None

    def get_watering(self):
        state = self.read_output("watering")
        return "watering", {"enabled": state}

    def set_watering(self, params):
        self.write_output("watering", params["enabled"])
        return self.get_watering()
    
    def get_lighting(self):
        state = self.read_output("lighting")
        return "lighting", {"enabled": state}

    def set_lighting(self, params):
        self.write_output("lighting", params["enabled"])
        return self.get_lighting()
    
    def get_heating(self):
        state = self.read_output("heating")
        return "heating", {"enabled": state}

    def set_heating(self, params):
        self.write_output("heating", params["enabled"])
        return self.get_heating()


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
        actuators.write_output("controller-indicator", self.settings["enabled"])
        return self.get()
    
    def run(self):
        actuators.write_output("system-indicator", True)
        actuators.write_output("controller-indicator", self.settings["enabled"])
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
                results.append(actuators.get_lighting())
                results.append(actuators.get_heating())
            elif path == "actuators/watering":
                results.append(actuators.get_watering())
            elif path == "actuators/lighting":
                results.append(actuators.get_lighting())
            elif path == "actuators/heating":
                results.append(actuators.get_heating())
            
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
            elif path == "actuators/lighting":
                if not controller.settings["enabled"]:
                    results.append(actuators.set_lighting(self.json))
                else:
                    self.respond_error(403, "Cannot set actuators while the controller is enabled.")
            elif path == "actuators/heating":
                if not controller.settings["enabled"]:
                    results.append(actuators.set_heating(self.json))
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
