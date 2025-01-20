name = "Keithley 2400"
short_name = "K2400"

def match_idn(idn: str):
    return "KEITHLEY INSTRUMENTS INC.,MODEL 2400" in idn

# Channel functions
from pyvisa.resources import Resource

def read_voltage(resource: Resource) -> float:
    response = resource.query("READ?")
    # Parse response as voltage is the first value
    voltage = float(response.split(',')[0])
    return voltage

def set_voltage(resource: Resource, value: float):
    command = f":SOUR:VOLT {value}"
    resource.write(command)

def read_current(resource: Resource) -> float:
    response = resource.query("READ?")
    # Parse response as current is the second value
    current = float(response.split(',')[1])
    return current

def set_current(resource: Resource, value: float):
    command = f":SOUR:CURR {value}"
    resource.write(command)

channels = [
    ("Voltage", "V", read_voltage, set_voltage),
    ("Current", "A", read_current, set_current),
]