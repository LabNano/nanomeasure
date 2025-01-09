from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
import visa
from layout import render_node
from classes import ChannelNode, node_classes
import state

is_first_frame = True

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

            if s_type == e_type:
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
                        output_node.outputs[o].connections.add((input_node, i))
                else:
                    showLabel("Incompatible types", imgui.ImVec4(0.5, 0.5, 0.5, 1))
                    ed.reject_new_item(imgui.ImVec4(0.5, 0.5, 0.5, 1), 2.0)

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
        ed.end_delete()
def render_link():
    for node in state.nodes:
        for o, out in enumerate(node.outputs):
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

def gui():
    global is_first_frame
    imgui.separator()
    ed.begin("Node Editor", imgui.ImVec2(0.0, 0.0))

    for node in state.nodes:
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
                state.nodes += [node()]
        imgui.end_popup()
    ed.resume()
    ed.end()
    is_first_frame = False

def main():
    from imgui_bundle import immapp
    visa.preview_thread = visa.PreviewThread(query_interval_ms=50)
    visa.preview_thread.start()

    for instrument in visa.find_resources():
        state.nodes += [ChannelNode(instrument)]
    

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