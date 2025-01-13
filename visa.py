import threading
import time
import importlib
import types
from typing import List, Set, Tuple, Callable
from glob import glob
import pyvisa
from pyvisa.resources import Resource
from collections import deque

rm = pyvisa.ResourceManager()

debug = True
preview_thread = None

modules = {}
for module in [m[:-3] for m in glob("drivers/*.py")]:
    try:
        modules[module] = importlib.import_module(module.replace("/","."))
    except:
        print("Failed to load module ", module)


instruments: Set['Instrument'] = set()
class Instrument:
    def __init__(self,address: str, resource: Resource, module: types.ModuleType):
        self.resource = resource
        self.module = module
        self.idn = resource.query("*IDN?") if resource else None
        self.address = address
        self.last_time = 0
        self.preview = False
        self.preview_buffer = deque(maxlen=300)
        self.preview_channel = 0
        self.add_instrument()

    def add_instrument(self):
        """Add a new instrument to the global list to be used by the thread."""
        global instruments
        try:
            self.resource = rm.open_resource(self.address)
            instruments.add(self) #Instrument will not be added if the connection fails
            print(f"Connected to: {self.resource.query('*IDN?')}")
        except Exception as e:
            print(f"Error connecting to {self.name}: {e}")

    @property
    def name(self):
        if hasattr(modules[self.module], "name"):
            return modules[self.module].name
        return self.idn
    
    @property
    def short_name(self):
        if hasattr(modules[self.module], "short_name"):
            return modules[self.module].short_name
        return self.name
    
    @property
    def channels(self) -> List[Tuple[str, str, Callable, Callable]]:
        if hasattr(modules[self.module], "channels"):
            return modules[self.module].channels
        return []

def find_resources() -> List[Instrument]:
    resources = []
    for r in rm.list_resources():
        if r.startswith("ASRL"):
            continue
        try:
            inst = rm.open_resource(r)
            idn = inst.query("*IDN?")
            for m in modules:
                try:
                    if modules[m].match_idn(idn):
                        resources = resources + [Instrument(r, inst, m)]
                except:
                    print("Failed to match ", modules[m].name)
        except:
            print("Failed to query", r)
        finally:
            inst.close()
    if debug and not resources:
        return [Instrument("TEST::INSTR", None, m) for m in modules]
    return resources

#KEITHLEY INSTRUMENTS INC.,MODEL 2100,1,01.08-01-01

def disable_preview():
    global instruments
    for inst in instruments:
        inst.preview = False
        inst.preview_buffer.clear()

class PreviewThread(threading.Thread):
    def __init__(self, query_interval_ms=50):
        super().__init__()
        self.query_interval = query_interval_ms / 1000.0
        self.keep_running = True

    def run(self):
        try:
            while self.keep_running:
                current_time = time.time()
                for inst in instruments:
                    if not inst.preview:
                        continue
                    # Check if enough time has passed to query this instrument
                    if current_time - inst.last_time >= self.query_interval:
                        try:
                            res = inst.channels[inst.preview_channel][2](inst.resource)
                            inst.preview_buffer.append(res)
                        except Exception as e:
                            print(f"Error querying {inst.name}: {e}")
                        inst.last_time = current_time

                time.sleep(0.01)  # Small sleep to prevent busy-waiting
        except Exception as e:
            print(f"Error: {e}")
        finally:
            disable_preview()
            print("Preview thread terminated.")

    def stop(self):
        """Stop the thread gracefully."""
        self.keep_running = False
