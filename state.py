import os
from imgui_bundle import imgui_node_editor as ed # type: ignore
from typing import List, Tuple
import pickle

from classes import Node, ID, ChannelNode

nodes: List[Node] = []

available_channels: List[ChannelNode] = []

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "save", "state.pkl")
def save_state():
    global nodes
    for n in nodes:
        if isinstance(n, ChannelNode):
            n.instrument.discard_resource()
    with open(file_path, "wb") as f:
        pickle.dump(nodes, f)
    for n in nodes:
        if isinstance(n, ChannelNode):
            n.instrument.restore_resource()

def load_state():
    global nodes
    try:
        with open(file_path, "rb") as f:
            nodes = pickle.load(f)
            ID._next_id = max(node.id for node in nodes) + 1
            for n in nodes:
                if isinstance(n, ChannelNode):
                    n.instrument.restore_resource()
    except FileNotFoundError:
        nodes = []

def get_node_by_id(id: int) -> Node:
    for node in nodes:
        if node.id == id:
            return node
    return None

def cantor_pairing(a: int, b: int) -> int:
        return (a + b) * (a + b + 1) // 2 + b
def reverse_cantor_pairing(z: int) -> Tuple[int, int]:
        w = int(((8 * z + 1) ** 0.5 - 1) / 2)
        t = (w * (w + 1)) // 2
        y = z - t
        x = w - y
        return x, y

def get_pin_id(node: Node, pin: int, kind: ed.PinKind) -> int:
    if kind == ed.PinKind.input:
        pin = pin * 2 + 1
    else:
        pin = pin * 2
    m = 1 << (31)
    return cantor_pairing(node.id, pin) | m
def reverse_pin_id(pin_id: int) -> Tuple[int, int, ed.PinKind]:
    m = 1 << 31
    pin_id &= ~m
    node_id, pin = reverse_cantor_pairing(pin_id)
    kind = ed.PinKind.input if pin % 2 == 1 else ed.PinKind.output
    pin = pin // 2
    return node_id, pin, kind

def get_link_id(input_id: int, output_id: int) -> int:
    m = 1 << 31
    input_id &= ~m
    output_id &= ~m
    return cantor_pairing(input_id, output_id)
def reverse_link_id(link_id: int) -> Tuple[int, int]:
    input_pin, output_pin = reverse_cantor_pairing(link_id)
    m = 1 << 31
    return (input_pin | m, output_pin | m)
