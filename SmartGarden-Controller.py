#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from threading import Thread
import time
import json
import subprocess


def _update_params(old, new):
    assert type(old) is type(new)
    for key in old.keys():
        if key in new:
            if type(old[key]) is dict:
                _update_params(old[key], new[key])
            old[key] = new[key]


class SmartGardenSensors:

    def __init__(self, config):
        self.config = config

    def get(self, sensor):
        path = f"/var/SmartGarden/{sensor}"

        data = {"timestamp": int(os.path.getmtime(path))}
        with open(path, "r") as f:
            data["value"] = float(f.read())
        data["units"] = self.config[sensor]["units"]

        return sensor, data


class SmartGardenActuators:

    def __init__(self, config):
        self.config = config

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

    def get(self, actuator):
        state = self.read_output(actuator)
        data = {"enabled": state}
        for k, v in self.config[actuator].items():
            data[k] = v
        return actuator, data

    def set(self, actuator, params):
        _update_params(self.config[actuator], params)
        if "enabled" in params:
            self.write_output(actuator, params["enabled"])
        return self.get(actuator)


class SmartGardenImage:

    def __init__(self, config):
        self.config = config

    def get(self):
        output = subprocess.check_output(["raspistill", "-o", "-", 
        "-w", str(self.config["width"]), "-h", str(self.config["height"])])
        return "image/jpeg", output

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
        
        controller_enabled = self.settings["enabled"]
        actuators.write_output("controller-indicator", controller_enabled)
        if not controller_enabled:
            for actuator in actuators.config.keys():
                actuators.set(actuator, {"enabled": False})
        
        return self.get()
    
    def run(self):
        actuators.write_output("system-indicator", True)
        actuators.write_output("controller-indicator", self.settings["enabled"])
        
        while True:
            if self.settings["enabled"]:
                try:
                
                    for actuator, params in actuators.config.items():
                        _, sensor_data = sensors.get(params["sensor"])
                        sensor_value = sensor_data["value"]
                        
                        new_state = None
                        if sensor_value <= params["threshold"] - params["deviation"]:
                            new_state = True
                        elif sensor_value > params["threshold"] + params["deviation"]:
                            new_state = False
                        
                        if new_state is not None:
                            actuators.set(actuator, {"enabled": new_state})
                
                except Exception as e:
                    print(e.args[0])

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

    def respond_content(self, content_type, data):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(data)

    @property
    def json(self):
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)
        params = json.loads(data)
        return params

    def do_GET(self):
        try:
            results = []

            path = self.path.strip("/").split("/")
            if path[0] == "":
                self.respond(204)

            elif path[0] == "sensors":
                if len(path) == 1:
                    for sensor in config["Sensors"].keys():
                        results.append(sensors.get(sensor))
                else:
                    results.append(sensors.get(path[1]))
            
            elif path[0] == "actuators":
                if len(path) == 1:
                    for actuator in config["Actuators"].keys():
                        results.append(actuators.get(actuator))
                else:
                    results.append(actuators.get(path[1]))

            elif path[0] == "controller":
                results.append(controller.get())
            
            elif path[0] == "image":
                self.respond_content(*image.get())

            else:
                self.respond_error(404, "Not Found")
            
            if results:
                self.respond(200, results)
        
        except Exception as e:
            self.respond_error(500, e.args[0])

    def do_PATCH(self):
        try:
            results = []

            path = self.path.strip("/").split("/")
            if path[0] == "":
                self.respond_error(405, "Method Not Allowed")
            
            elif path[0] == "sensors":
                self.respond_error(405, "Method Not Allowed")
            
            elif path[0] == "image":
                self.respond_error(405, "Method Not Allowed")

            elif path[0] == "actuators":
                if len(path) == 1:
                    self.respond_error(405, "Method Not Allowed")
                else:
                    results.append(actuators.set(path[1], self.json))
            
            elif path[0] == "controller":
                results.append(controller.set(self.json))

            else:
                self.respond_error(404, "Not Found")
            
            if results:
                self.respond(200, results)
        
        except Exception as e:
            self.respond_error(500, e.args[0])


def main():
    global sensors, actuators, image, controller, config
    with open("/etc/SmartGarden/config.json", "r") as f:
        config = json.load(f)
    sensors = SmartGardenSensors(config["Sensors"])
    actuators = SmartGardenActuators(config["Actuators"])
    image = SmartGardenImage(config["Image"])
    controller = SmartGardenController(config["Controller"])
    controller.start()

    httpd = HTTPServer((config["API"]["bind_ip"], config["API"]["bind_port"]), SmartGardenHTTPRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
