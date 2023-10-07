#!/usr/bin/env python3

import os

from flask import Flask, Response, jsonify

from sps30 import SPS30

device = os.environ["SERIAL_DEVICE"] or "/dev/ttyUSB0"
print(f"Using device: {device}")
sensor = SPS30(device)
sensor.start_measurement()
app = Flask(__name__)


@app.route("/measurements")
def measurements() -> Response:
    measurement = sensor.read_measured_values()
    return jsonify(measurement)
