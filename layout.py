
from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List, Tuple
from classes import Node
import state


def render_pin(node: Node, pin: int, kind: ed.PinKind = ed.PinKind.input):
    pin_id = ed.PinId(state.get_pin_id(node, pin, kind))
    if kind == ed.PinKind.input:
        pin_type = node.inputs[pin]
    else:
        pin_type = node.outputs[pin]
    size = 8
    ed.begin_pin(pin_id, kind)
    imgui.push_id(str(pin_id.id()))
    imgui.begin_horizontal("pin")
    if kind == ed.PinKind.output:
        ed.pin_pivot_alignment(imgui.ImVec2(1, 0.5))
        imgui.align_text_to_frame_padding()
        imgui.text(pin_type.name)
        # imgui.same_line(0)
    center = imgui.get_cursor_pos()
    center.y += imgui.get_frame_height() / 2
    if kind == ed.PinKind.input:
        center.x -= size
        ed.pin_pivot_alignment(imgui.ImVec2(0, 0.5))
        imgui.align_text_to_frame_padding()
        imgui.text(pin_type.name)

    imgui.get_window_draw_list().add_circle_filled(center, size/2, pin_type.color)
    imgui.end_horizontal()
    imgui.pop_id()
    ed.end_pin()


def node_header(node_id: ed.NodeId, title: str) -> Tuple[imgui.ImVec2, imgui.ImVec2]:
    imgui.text(title)
    imgui.spacing()
    padd = ed.get_style().node_padding
    rmin = ed.get_node_position(node_id)
    rmax = ed.get_node_position(node_id)
    s = ed.get_node_size(node_id)
    rmax.x += s.x
    h = imgui.get_item_rect_max().y - imgui.get_item_rect_min().y
    rmax.y += h + padd.y + 4
    return rmin, rmax


def render_node(node: Node) -> ed.NodeId:
    node_id = ed.NodeId(node.id)
    imgui.push_id(node.id)

    ed.begin_node(node_id)
    imgui.begin_vertical("node")

    rmin, rmax = node_header(node_id, node.title)

    layout = NodeLayout(node)
    node.content(layout)
    layout.render_content()


    imgui.end_vertical()
    ed.end_node()

    ed.get_node_background_draw_list(node_id).add_rect_filled(rmin, rmax, node.color, ed.get_style().node_rounding, imgui.ImDrawFlags_.round_corners_top)
    imgui.pop_id()
    return node_id

def begin_pins(n: int):
    def _begin_pins():
        imgui.push_id(n)
        imgui.begin_horizontal(f"content")
        imgui.spring(0, 0)
    return _begin_pins

def _end_pin():
    imgui.spring(1, 0)
    imgui.end_vertical()

def _end_pins():
    imgui.end_horizontal()
    imgui.pop_id()

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
        self.contents_count = 0

    def _close_pins(self):
        if self.previous_was_pin:
            self.instructions += [
                _end_pin,
                _end_pins
            ]
        self.previous_was_pin = 0


    def add_input(self, id: int):
        if self.previous_was_pin == 0:
            self.contents_count += 1
            self.instructions += [
                begin_pins(self.contents_count),
                _begin_input
            ]
        if self.previous_was_pin == 2:
            self.contents_count += 1
            self.instructions += [
                _end_pin,
                _end_pins,
                begin_pins(self.contents_count),
                _begin_input,
            ]
        def f():
            render_pin(self.node, id, ed.PinKind.input)
        self.instructions += [f]
        self.previous_was_pin = 1

    def add_output(self, id: int):
        if self.previous_was_pin == 0:
            self.contents_count += 1
            self.instructions += [
                begin_pins(self.contents_count),
                _begin_output,
            ]
        if self.previous_was_pin == 1:
            self.instructions += [
                _end_pin,
                _begin_output
            ]
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
          