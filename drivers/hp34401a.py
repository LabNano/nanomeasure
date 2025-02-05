name = "DMM HP34401A"
short_name = "HP34401A"

def match_idn(idn: str):
    return "HEWLETT-PACKARD,34401A" in idn

# Channel functions
from pyvisa.resources import Resource

def read_voltage(resource: Resource) -> float:
    response = resource.query("READ?")
    voltage = float(response)
    return voltage

channels = [
    ("Voltage", "V", read_voltage, None),
]


def on_load(resource: Resource):
    pass

def on_measure(resource: Resource):
    pass