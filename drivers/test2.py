import random

name = "Test Instrument 2"
short_name = "TEST 2"

def match_idn(idn: str):
    return idn.startswith("TEST")


# Channel functions
from pyvisa.resources import Resource
def read_voltage(resource: Resource) -> float:
    return random.random()
def set_voltage(resource: Resource, value: float):
    pass
def read_current(resource: Resource) -> float:
    return random.random()
def read_resistance(resource: Resource) -> float:
    return random.random()


channels = [
    ("Voltage", "V", read_voltage, set_voltage),
    ("Current", "A", read_current, None),
    ("Resistance", "Ω", read_resistance, None),
]