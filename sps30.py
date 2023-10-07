import struct
from dataclasses import dataclass

import serial


@dataclass
class SendPacket:
    address: int
    command: int
    length: int
    data: bytes
    checksum: int

    def pack(self) -> bytes:
        header = bytes([
            0x7e,
            self.address,
            self.command,
            self.length,
        ])
        footer = bytes([self.checksum, 0x7e])
        return header + self.data + footer


@dataclass
class ReceivePacket:
    address: int
    command: int
    state: int
    length: int
    data: bytes
    checksum: int

    def is_empty(self) -> bool:
        return self.length == 0 and len(self.data) == 0


SERIAL_BAUD_RATE = 115200
CMD_START_MEASUREMENT = 0x00
CMD_READ_MEASURED_VALUES = 0x03

MEASUREMENT_START_RESPONSE: ReceivePacket = ReceivePacket(
    address=0x00,
    command=0x00,
    state=0x00,
    length=0x00,
    data=b"",
    checksum=0x00,
)


@dataclass
class Measurement:
    mass_pm1: float
    mass_pm25: float
    mass_pm4: float
    mass_pm10: float
    number_pm05: float
    number_pm1: float
    number_pm25: float
    number_pm4: float
    number_pm10: float
    typical_size: float


def _unpack_measurement_from_bytes(data: bytes) -> Measurement:
    big_endian_floats = ">ffffffffff"
    unpacked = struct.unpack(big_endian_floats, data)
    return Measurement(*unpacked)


class SPS30:
    device: serial.Serial

    def __init__(self, path: str):
        self.device = serial.Serial(path, SERIAL_BAUD_RATE)

    def close(self) -> None:
        self.device.close()

    def start_measurement(self) -> None:
        packet = SendPacket(address=0x00,
                            command=CMD_START_MEASUREMENT,
                            length=0x02,
                            data=bytes([0x01, 0x03]),
                            checksum=0xf9)
        self._send_packet(packet)
        response = self._receive_packet()
        if response != MEASUREMENT_START_RESPONSE:
            raise Exception(f"invalid response: {response}")

    def read_measured_values(self, max_retries: int = 100) -> Measurement:
        for _ in range(max_retries):
            packet = SendPacket(address=0x00,
                                command=CMD_READ_MEASURED_VALUES,
                                length=0x00,
                                data=b"",
                                checksum=0xfc)
            self._send_packet(packet)
            response = self._receive_packet()
            if not response.is_empty():
                return _unpack_measurement_from_bytes(response.data)
        raise Exception(f"no response after {max_retries} retries")

    def _read_stuffed_byte(self) -> bytes:
        datum: bytes = self.device.read()
        if datum == b"\x7d":
            next_datum = self.device.read()
            if next_datum == b"\x5e":
                return b"\x7e"
            if next_datum == b"\x31":
                return b"\x11"
            if next_datum == b"\x33":
                return b"\x13"
            if next_datum == b"\x5d":
                return b"\x7d"
            raise Exception(f"Invalid byte stuffing: {next_datum}")
        return datum

    def _read_bytes(self, length: int) -> bytes:
        data = b""
        for _ in range(length):
            data += self._read_stuffed_byte()
        return data

    def _receive_packet(self) -> ReceivePacket:
        start = self.device.read()
        if start != b"~":
            raise Exception(f"Invalid stop byte: {start}")
        address = self._read_stuffed_byte()
        command = self._read_stuffed_byte()
        state = self._read_stuffed_byte()
        length = int.from_bytes(self._read_stuffed_byte())
        data = self._read_bytes(length)
        checksum = self._read_stuffed_byte()
        stop = self.device.read()
        if stop != b"~":
            print(f"""
                start: {start!r}
                address: {address!r}
                command: {command!r}
                state: {state!r}
                length: {length}
                data:
                      {data!r}
                      {data.hex()}
                checksum: {checksum!r}
                stop: {stop!r}
                """)
            raise Exception(f"Invalid stop byte: {stop}")
        return ReceivePacket(
            address=int.from_bytes(address),
            command=int.from_bytes(command),
            state=int.from_bytes(command),
            length=length,
            data=data,
            checksum=int.from_bytes(command),
        )

    def _send_packet(self, packet: SendPacket) -> None:
        self.device.write(packet.pack())
