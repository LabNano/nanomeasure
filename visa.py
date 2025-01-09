import threading
import time
import importlib
import types
from typing import List, Set
from glob import glob
import pyvisa
from pyvisa.resources import Resource
from collections import deque

rm = pyvisa.ResourceManager()

debug = True
preview_thread = None

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

    @property
    def name(self):
        if hasattr(self.module, "name"):
            return self.module.name
        return self.idn
    
    @property
    def short_name(self):
        if hasattr(self.module, "short_name"):
            return self.module.short_name
        return self.name
    
    @property
    def channels(self):
        if hasattr(self.module, "channels"):
            return self.module.channels
        return []

def find_resources() -> List[Instrument]:
    modules = []
    for module in [m[:-3] for m in glob("drivers/*.py")]:
        try:
            modules = modules + [importlib.import_module(module.replace("/","."))]
        except:
            print("Failed to load module ", module)

    resources = []
    for r in rm.list_resources():
        if r.startswith("ASRL"):
            continue
        try:
            inst = rm.open_resource(r)
            idn = inst.query("*IDN?")
            for m in modules:
                try:
                    if m.match_idn(idn):
                        resources = resources + [Instrument(r, inst, m)]
                except:
                    print("Failed to match ", m.name)
        except:
            print("Failed to query", r)
        finally:
            inst.close()
    if debug and not resources:
        return [Instrument("TEST::INSTR", None, m) for m in modules]
    return resources

#KEITHLEY INSTRUMENTS INC.,MODEL 2100,1,01.08-01-01


class PreviewThread(threading.Thread):
    def __init__(self, query_interval_ms=50):
        super().__init__()
        self.query_interval = query_interval_ms / 1000.0
        self.keep_running = True
        self.instruments: Set[Instrument] = set()

    def add_instrument(self, inst: Instrument):
        """Add a new instrument to the thread."""
        try:
            inst.resource = rm.open_resource(inst.address)
            self.instruments.add(inst)
            print(f"Connected to: {inst.resource.query('*IDN?')}")
        except Exception as e:
            print(f"Error connecting to {inst.name}: {e}")

    def run(self):
        try:
            while self.keep_running:
                current_time = time.time()

                for inst in self.instruments:
                    if not inst.preview:
                        continue
                    # Check if enough time has passed to query this instrument
                    if current_time - inst.last_time >= self.query_interval:
                        res = inst.channels[inst.preview_channel][2](inst.resource)
                        inst.preview_buffer.append(res)
                        inst.last_time = current_time

                time.sleep(0.01)  # Small sleep to prevent busy-waiting
        except Exception as e:
            print(f"Error: {e}")
        finally:
            for inst in self.instruments:
                inst.preview = False
                # inst.resource.close()
            print("Preview thread terminated.")

    def stop(self):
        """Stop the thread gracefully."""
        self.keep_running = False
