
from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List, Tuple
from classes import Node, node_classes
import state
import measure


def showLabel(label: str, color: imgui.ImVec4):
    imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() - imgui.get_text_line_height())
    size = imgui.calc_text_size(label)
    padd = imgui.get_style().frame_padding
    spac = imgui.get_style().item_spacing
    imgui.set_cursor_pos(imgui.get_cursor_pos() + imgui.ImVec2(spac.x, -spac.y))
    recmin = imgui.get_cursor_screen_pos() - padd
    recmax = imgui.get_cursor_screen_pos() + size + padd
    imgui.get_window_draw_list().add_rect_filled(recmin, recmax, imgui.get_color_u32(color), size.y * 0.15)
    imgui.text_unformatted(label)

def handle_menu():
    ed.suspend()
    if ed.show_background_context_menu():
        imgui.open_popup("Add Node")

    if imgui.begin_popup("Add Node"):
        imgui.text("Add Node")
        imgui.separator()
        for node in node_classes:
            # imgui.push_style_color(imgui.Col_.text, node.color)
            if imgui.menu_item_simple(node.title):
                state.nodes += [node()]
                state.save_state()
            # imgui.pop_style_color()
        imgui.end_popup()
    ed.resume()

create_color = imgui.ImVec4(1, 1, 1, 1)
def create_links():
    global create_color
    ed.push_style_color(ed.StyleColor.hov_link_border, imgui.ImVec4(1, 1, 1, .8))
    ed.push_style_color(ed.StyleColor.sel_link_border, imgui.ImVec4(1, 1, 1, .5))
    if ed.begin_create(create_color):
        start_id = ed.PinId()
        end_id = ed.PinId()
        if ed.query_new_link(start_id, end_id):
          if start_id:
            start_node_id, s_pin, s_type= state.reverse_pin_id(start_id.id())
            if s_type == ed.PinKind.input:
                create_color = imgui.color_convert_u32_to_float4(state.get_node_by_id(start_node_id).inputs[s_pin].color)
            else:
                create_color = imgui.color_convert_u32_to_float4(state.get_node_by_id(start_node_id).outputs[s_pin].color)
              
          if start_id and end_id:
            start_node_id, s_pin, s_type= state.reverse_pin_id(start_id.id())
            end_node_id, e_pin, e_type = state.reverse_pin_id(end_id.id())

            if s_type == e_type or start_node_id == end_node_id:
                # showLabel("Can't connect pins of the same kind",   imgui.ImVec4(0.5, 0.5, 0.5, 1))
                ed.reject_new_item(imgui.ImVec4(0.5, 0.5, 0.5, 1), 2.0)
            else:
                if s_type == ed.PinKind.input:
                    input_node = state.get_node_by_id(start_node_id)
                    i = s_pin
                    output_node = state.get_node_by_id(end_node_id)
                    o = e_pin
                else:
                    input_node = state.get_node_by_id(end_node_id)
                    i = e_pin
                    output_node = state.get_node_by_id(start_node_id)
                    o = s_pin

                if isinstance(output_node.outputs[o], type(input_node.inputs[i])):
                    create_color = imgui.color_convert_u32_to_float4(input_node.inputs[i].color)
                    if ed.accept_new_item():
                        if len(input_node.inputs[i].connections) > 0:
                            old_conn = list(input_node.inputs[i].connections)[0]
                            old_conn[0].outputs[old_conn[1]].connections.remove((input_node, i))
                            input_node.inputs[i].connections.clear()
                        input_node.inputs[i].connections.add((output_node, o))
                        input_node.on_connect(i, ed.PinKind.input)
                        output_node.outputs[o].connections.add((input_node, i))
                        output_node.on_connect(o, ed.PinKind.output)
                        state.save_state()
                else:
                    showLabel("Incompatible types", imgui.ImVec4(0.5, 0.5, 0.5, 1))
                    ed.reject_new_item(imgui.ImVec4(0.5, 0.5, 0.5, 1), 2.0)
        # elif ed.accept_new_item():
        #     imgui.open_popup("Add Node")
        ed.end_create()

    if ed.begin_delete():
        deleted_link_id = ed.LinkId()
        while ed.query_deleted_link(deleted_link_id):
                if ed.accept_deleted_item():
                    input_pin_id, output_pin_id = state.reverse_link_id(deleted_link_id.id())
                    input_node_id, i, _ = state.reverse_pin_id(input_pin_id)
                    output_node_id, o, _ = state.reverse_pin_id(output_pin_id)
                    input_node = state.get_node_by_id(input_node_id)
                    output_node = state.get_node_by_id(output_node_id)
                    input_node.inputs[i].connections.clear()
                    output_node.outputs[o].connections.remove((input_node, i))
                    state.save_state()

        deleted_node_id = ed.NodeId()
        while ed.query_deleted_node(deleted_node_id):
            if ed.accept_deleted_item():
                node = state.get_node_by_id(deleted_node_id.id())
                for i,inp in enumerate(node.inputs):
                    for c in inp.connections:
                        c[0].outputs[c[1]].connections.remove((node, i))
                for o,out in enumerate(node.outputs):
                    for c in out.connections:
                        c[0].inputs[c[1]].connections.remove((node, o))
                state.nodes.remove(node)
                state.save_state()
        ed.end_delete()
def render_links():
    for node in state.nodes:
        for o, out in enumerate(node.outputs):
            # print(out.name, out.connections)
            for connection in out.connections:
                for i, inp in enumerate(connection[0].inputs):
                    if i != connection[1]:
                        continue
                    input_id = ed.PinId(state.get_pin_id(connection[0], i, ed.PinKind.input))
                    output_id = ed.PinId(state.get_pin_id(node, o, ed.PinKind.output))
                    ed.link(
                        ed.LinkId(state.get_link_id(input_id.id(), output_id.id())),
                        input_id,
                        output_id,
                        imgui.color_convert_u32_to_float4(inp.color),
                        2.0
                    )

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
    mn = imgui.get_item_rect_min()
    mx = imgui.get_item_rect_max()
    mx.y += 4
    if kind == ed.PinKind.output:
        mx.x = center.x
    else:
        mn.x = center.x
    ed.pin_rect(mn, mx)
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
    
    imgui.begin_disabled(measure.is_measuring)
    layout = NodeLayout(node)
    node.content(layout)
    layout.render_content()
    imgui.end_disabled()

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
          