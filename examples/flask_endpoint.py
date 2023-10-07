#!/usr/bin/env python3

from flask import Flask, Response, jsonify

from sps30 import SPS30

sensor = SPS30("/dev/ttyUSB0")
sensor.start_measurement()
app = Flask(__name__)


@app.route("/measurements")
def measurements() -> Response:
    measurement = sensor.read_measured_values()
    return jsonify(measurement)
