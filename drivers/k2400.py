# Channel functions
from pyvisa.resources import Resource

name = "Keithley 2400"
short_name = "K2400"

def match_idn(idn: str):
    return "KEITHLEY INSTRUMENTS INC.,MODEL 2400" in idn

def read_voltage(resource: Resource) -> float:
    response = resource.query("READ?")
    voltage = float(response.split(',')[0])
    return voltage

def set_voltage(resource: Resource, value: float):
    command = f":SOUR:VOLT {value}"
    resource.write(command)


def read_current(resource: Resource) -> float:
    response = resource.query("READ?")
    current = float(response.split(',')[1])
    return current

def set_current(resource: Resource, value: float):
    command = f":SOUR:CURR {value}"
    resource.write(command)

channels = [
    ("Voltage", "V", read_voltage, set_voltage),
    ("Current", "A", read_current, set_current),
]


def on_load(resource: Resource):
    print("Loaded K2400")
    resource.write('*RST')
    resource.write(':sour:func volt')
    resource.write(':sour:volt:rang 200')
    resource.write(':sens:curr:prot 100e-6')
    resource.write(':sens:curr:rang 100e-6')
    resource.write(':outp on')
    pass

def on_measure(resource: Resource):
    pass