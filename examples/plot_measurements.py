from matplotlib import pyplot as plt

from sps30 import SPS30

if __name__ == "__main__":
    plt.axis()
    sensor = SPS30("/dev/ttyUSB0")
    sensor.start_measurement()
    for i in range(100):
        measurement = sensor.read_measured_values()
        print(measurement)
        plt.scatter(i, measurement.mass_pm25, color="red")
        plt.scatter(i, measurement.number_pm25, color="blue")
        plt.pause(0.05)
    sensor.close()
    plt.show()
