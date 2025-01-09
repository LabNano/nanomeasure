from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List, Tuple
import visa
from structure import ChannelNode, Node, node_classes

is_first_frame = True
nodes: List[Node] = []

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

def render_pin(node: Node, pin: int, kind: ed.PinKind = ed.PinKind.input):
    pin_id = ed.PinId(get_pin_id(node, pin, kind))
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
            

def render_node(node: Node):
    node_id = ed.NodeId(node.id)
    imgui.push_id(node.id)
    if is_first_frame:
        ed.set_node_position(node_id, imgui.ImVec2(0, 0))

    ed.begin_node(node_id)
    imgui.begin_vertical("node")

    rmin, rmax = node_header(node_id, node.title)

    imgui.begin_horizontal("content")
    imgui.spring(0, 0)
    imgui.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0)
    for p in range(len(node.inputs)):
        render_pin(node, p, ed.PinKind.input)
    imgui.spring(1, 0)
    imgui.end_vertical()

    imgui.spring(1)    

    imgui.begin_vertical("outputs", imgui.ImVec2(0, 0), 1.0)
    for p in range(len(node.outputs)):
        render_pin(node, p, ed.PinKind.output)
    imgui.end_vertical()
    imgui.end_horizontal()

    node.drawExtras()

    imgui.end_vertical()
    ed.end_node()

    ed.get_node_background_draw_list(node_id).add_rect_filled(rmin, rmax, node.color, ed.get_style().node_rounding, imgui.ImDrawFlags_.round_corners_top)
    imgui.pop_id()

def render_link():
    for node in nodes:
        for o, out in enumerate(node.outputs):
            for connection in out.connections:
                for i, inp in enumerate(connection[0].inputs):
                    if i != connection[1]:
                        continue
                    input_id = ed.PinId(get_pin_id(connection[0], i, ed.PinKind.input))
                    output_id = ed.PinId(get_pin_id(node, o, ed.PinKind.output))
                    ed.link(
                        ed.LinkId(get_link_id(input_id.id(), output_id.id())),
                        input_id,
                        output_id,
                        imgui.color_convert_u32_to_float4(inp.color),
                        2.0
                    )

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
            start_node_id, s_pin, s_type= reverse_pin_id(start_id.id())
            if s_type == ed.PinKind.input:
                create_color = imgui.color_convert_u32_to_float4(get_node_by_id(start_node_id).inputs[s_pin].color)
            else:
                create_color = imgui.color_convert_u32_to_float4(get_node_by_id(start_node_id).outputs[s_pin].color)
              
          if start_id and end_id:
            start_node_id, s_pin, s_type= reverse_pin_id(start_id.id())
            end_node_id, e_pin, e_type = reverse_pin_id(end_id.id())

            if s_type == e_type:
                # showLabel("Can't connect pins of the same kind",   imgui.ImVec4(0.5, 0.5, 0.5, 1))
                ed.reject_new_item(imgui.ImVec4(0.5, 0.5, 0.5, 1), 2.0)
            else:
                if s_type == ed.PinKind.input:
                    input_node = get_node_by_id(start_node_id)
                    i = s_pin
                    output_node = get_node_by_id(end_node_id)
                    o = e_pin
                else:
                    input_node = get_node_by_id(end_node_id)
                    i = e_pin
                    output_node = get_node_by_id(start_node_id)
                    o = s_pin

                if isinstance(output_node.outputs[o], type(input_node.inputs[i])):
                    create_color = imgui.color_convert_u32_to_float4(input_node.inputs[i].color)
                    if ed.accept_new_item():
                        if len(input_node.inputs[i].connections) > 0:
                            old_conn = list(input_node.inputs[i].connections)[0]
                            old_conn[0].outputs[old_conn[1]].connections.remove((input_node, i))
                            input_node.inputs[i].connections.clear()
                        input_node.inputs[i].connections.add((output_node, o))
                        output_node.outputs[o].connections.add((input_node, i))
                else:
                    showLabel("Incompatible types", imgui.ImVec4(0.5, 0.5, 0.5, 1))
                    ed.reject_new_item(imgui.ImVec4(0.5, 0.5, 0.5, 1), 2.0)

        ed.end_create()

    if ed.begin_delete():
        deleted_link_id = ed.LinkId()
        while ed.query_deleted_link(deleted_link_id):
                if ed.accept_deleted_item():
                    input_pin_id, output_pin_id = reverse_link_id(deleted_link_id.id())
                    input_node_id, i, _ = reverse_pin_id(input_pin_id)
                    output_node_id, o, _ = reverse_pin_id(output_pin_id)
                    input_node = get_node_by_id(input_node_id)
                    output_node = get_node_by_id(output_node_id)
                    input_node.inputs[i].connections.clear()
                    output_node.outputs[o].connections.remove((input_node, i))
        ed.end_delete()

def gui():
    global is_first_frame
    global nodes
    imgui.separator()
    ed.begin("Node Editor", imgui.ImVec2(0.0, 0.0))

    for node in nodes:
        render_node(node)

    render_link()

    create_links()
    
    ed.suspend()
    if ed.show_background_context_menu():
        imgui.open_popup("Add Node")

    if imgui.begin_popup("Add Node"):
        imgui.text("Add Node")
        imgui.separator()
        for node in node_classes:
            if imgui.menu_item_simple(node.title):
                nodes += [node()]
        imgui.end_popup()
    ed.resume()
    ed.end()
    is_first_frame = False

def main():
    global nodes
    from imgui_bundle import immapp
    visa.preview_thread = visa.PreviewThread(query_interval_ms=50)
    visa.preview_thread.start()

    for instrument in visa.find_resources():
        nodes += [ChannelNode(instrument)]
    

    immapp.run(
        gui,
        with_markdown=True,
        with_node_editor=True,
        window_size=(800, 600),
        window_title="Node Editor",
    )

    print("Stopping preview thread...")
    visa.preview_thread.stop()

if __name__ == "__main__":
    main()