name = "Keithley 2100"
short_name = "K2100"

def match_idn(idn: str):
    return idn.startswith("KEITHLEY INSTRUMENTS INC.,MODEL 2100")


# Channel functions
from pyvisa.resources import Resource
def read_voltage(resource: Resource) -> float:
    r = resource.query("MEAS:VOLT:DC? DEF,DEF")
    return float(r)
def set_voltage(resource: Resource, value: float):
    pass
def read_current(resource: Resource) -> float:
    r = resource.query("MEAS:CURR:DC? DEF,DEF")
    return float(r)
def read_resistance(resource: Resource) -> float:
    r = resource.query("MEAS:RES? DEF,DEF")
    return float(r)


channels = [
    ("Voltage", "V", read_voltage, set_voltage),
    ("Current", "A", read_current, None),
    # ("Resistance", "Ω", read_resistance, None),
]