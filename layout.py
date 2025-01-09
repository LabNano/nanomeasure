
from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List
from structure import Node

def _begin_pins():
    imgui.begin_horizontal("content")
    imgui.spring(0, 0)

def _end_pin():
    imgui.spring(1, 0)
    imgui.end_vertical()

def _end_pins():
    imgui.end_horizontal()

def _begin_input():
    imgui.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0)

def _begin_output():
    imgui.spring(1)
    imgui.begin_vertical("outputs", imgui.ImVec2(0, 0), 1.0)

class NodeLayout():
    def __init__(self, node: Node):
        self.instructions: List[function] = []
        self.previous_was_pin = 0
        self.node = node

    def _close_pins(self):
        if self.previous_was_pin:
            self.instructions += [
                _end_pin,
                _end_pins
            ]
        self.previous_was_pin = 0


    def add_input(self, id: int):
        if self.previous_was_pin == 0:
            self.instructions += [
                _begin_pins,
                _begin_input
            ]
        if self.previous_was_pin == 2:
            self.instructions += [
                _end_pin,
                _end_pins,
                _begin_pins,
                _begin_input,
            ]
        from node import render_pin
        def f():
            render_pin(self.node, id, ed.PinKind.input)
        self.instructions += [f]
        self.previous_was_pin = 1

    def add_output(self, id: int):
        if self.previous_was_pin == 0:
            self.instructions += [
                _begin_pins,
                _begin_output,
            ]
        if self.previous_was_pin == 1:
            self.instructions += [
                _end_pin,
                _begin_output
            ]
        from node import render_pin
        def f():
            render_pin(self.node, id, ed.PinKind.output)
        self.instructions += [f]
        self.previous_was_pin = 2

    def add_content(self, f):
        self._close_pins()
        self.instructions += [f]

    def render_content(self):
        for i, inst in enumerate(self.instructions):
            inst()
        if self.previous_was_pin:
            _end_pin()
            _end_pins()
            self.previous_was_pin = 0
          