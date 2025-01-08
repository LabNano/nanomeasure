from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List
import visa
from structure import ChannelNode, Node

is_first_frame = True
nodes: List[Node] = []

def cantor_pairing(a: int, b: int) -> int:
    return (a + b) * (a + b + 1) // 2 + b

def create_pin(node: Node, pin: int, kind: ed.PinKind = ed.PinKind.input):
    m1 = 1 << (31)
    m2 = 1 << (30)
    if kind == ed.PinKind.input:
        pin_id = ed.PinId(cantor_pairing(node.id, pin) | m1 | m2)
        pin_name, pin_type = node.inputs[pin]
    else:
        pin_id = ed.PinId((cantor_pairing(node.id, pin) | m1) & ~m2)
        pin_name, pin_type = node.outputs[pin]
    size = 8
    ed.begin_pin(pin_id, kind)
    if kind == ed.PinKind.output:
        ed.pin_pivot_alignment(imgui.ImVec2(1, 0.5))
        imgui.align_text_to_frame_padding()
        imgui.text(pin_name)
        imgui.same_line(0)
    center = imgui.get_cursor_pos()
    center.y += imgui.get_frame_height() / 2
    if kind == ed.PinKind.input:
        center.x -= size
        ed.pin_pivot_alignment(imgui.ImVec2(0, 0.5))
        imgui.align_text_to_frame_padding()
        imgui.text(pin_name)

    imgui.get_window_draw_list().add_circle_filled(center, size/2, node.color)
    ed.end_pin()

def create_node(node: Node):
    node_id = ed.NodeId(node.id)
    if is_first_frame:
        ed.set_node_position(node_id, imgui.ImVec2(0, 0))

    ed.begin_node(node_id)
    imgui.begin_vertical("node")
    imgui.text(node.title)
    imgui.spacing()
    padd = ed.get_style().node_padding
    rmin = ed.get_node_position(node_id)
    rmax = ed.get_node_position(node_id)
    s = ed.get_node_size(node_id)
    rmax.x += s.x
    h = imgui.get_item_rect_max().y - imgui.get_item_rect_min().y
    rmax.y += h + padd.y + 4


    imgui.begin_horizontal("content")
    imgui.spring(0, 0)
    imgui.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0)
    for p in range(len(node.inputs)):
        create_pin(node, p, ed.PinKind.input)
    imgui.spring(1, 0)
    imgui.end_vertical()

    imgui.spring(1)    

    imgui.begin_vertical("outputs", imgui.ImVec2(0, 0), 1.0)
    for p in range(len(node.outputs)):
        create_pin(node, p, ed.PinKind.output)
    imgui.end_vertical()
    imgui.end_horizontal()

    node.drawExtras()

    imgui.end_vertical()
    ed.end_node()

    ed.get_node_background_draw_list(node_id).add_rect_filled(rmin, rmax, node.color, ed.get_style().node_rounding, imgui.ImDrawFlags_.round_corners_top)

def gui():
    global is_first_frame
    global nodes
    imgui.separator()
    ed.begin("Node Editor", imgui.ImVec2(0.0, 0.0))

    for node in nodes:
        create_node(node)

    # if is_first_frame:
    #     ed.navigate_to_content(0.0)

    if ed.begin_create():
        ed.end_create()

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