from imgui_bundle import imgui, immapp, hello_imgui, imgui_node_editor as ed # type: ignore
import visa
from layout import render_node, render_links, create_links, handle_menu
from classes import ChannelNode
import measure
import state

def make_tab_visible(name: str):
    window = imgui.internal.find_window_by_name(name)
    if not window or not window.dock_node or not window.dock_node.tab_bar:
        return
    window.dock_node.tab_bar.next_selected_tab_id = window.tab_id

is_first_frame = True

_selected_node = 0
def gui():
    global is_first_frame
    global _nodes_selected
    global _selected_node
    dock_id = imgui.get_id("DockSpace")
    imgui.dock_space(dock_id, imgui.ImVec2(0, 0))
    
    if is_first_frame:
        imgui.internal.dock_builder_remove_node(dock_id)
        imgui.internal.dock_builder_add_node(dock_id)
        imgui.internal.dock_builder_set_node_size(dock_id, imgui.get_main_viewport().size)

        imgui.spacing()
        ids = imgui.internal.dock_builder_split_node(dock_id, imgui.Dir.right, 0.25)
        imgui.internal.dock_builder_dock_window("Node Editor", ids.id_at_opposite_dir)
        imgui.internal.dock_builder_dock_window("Measurement Info", ids.id_at_dir)
        imgui.internal.dock_builder_dock_window("Properties", ids.id_at_dir)
        imgui.internal.dock_builder_dock_window("Measure", ids.id_at_opposite_dir)
        # t = imgui.internal.dock_builder_add_node(dock_id)


        imgui.internal.dock_builder_finish(dock_id)
    
    imgui.begin("Node Editor")
    ed.begin("Node Editor")
    for node in state.nodes:
        render_node(node)
    render_links()
    if not measure.is_measuring:
        create_links()
        handle_menu()

    # Those functions are nor properly ported. It may cause segfaults
    s = ed.NodeId()
    _objects_selected = ed.get_selected_object_count()
    _nodes_selected = ed.get_selected_nodes(s, _objects_selected)
    _old_node = _selected_node
    if not _nodes_selected:
        _selected_node = None
    _selected_node = s.id()
    if _selected_node != _old_node:
        if isinstance(state.get_node_by_id(s.id()), ChannelNode):
            make_tab_visible("Properties")
        else:
            make_tab_visible("Measurement Info")

    if is_first_frame:
        ed.navigate_to_content(0.0)

    ed.end()
    imgui.end()

    imgui.begin("Measurement Info")
    measure.render_preview()
    imgui.end()

    imgui.begin("Measure")
    imgui.end()

    imgui.begin("Properties")
    imgui.end()

    if is_first_frame:
        imgui.set_window_focus("Measurement Info")
        imgui.set_window_focus("Node Editor")
        is_first_frame = False


def main():
    visa.preview_thread = visa.PreviewThread(query_interval_ms=50)
    visa.preview_thread.start()

    state.load_state()
    if not state.nodes:
        for instrument in visa.find_resources():
            state.nodes += [ChannelNode(instrument)]


    params = immapp.SimpleRunnerParams(
        gui,
        window_title="Nano Measure",
    ).to_runner_params()
    params.imgui_window_params.enable_viewports = True
    params.ini_filename = "save/layout.ini"
    # Remove this line if negative performance impact is observed
    params.dpi_aware_params = hello_imgui.DpiAwareParams(font_rendering_scale=0.25)
    params.app_window_params.window_geometry.full_screen_mode = hello_imgui.FullScreenMode.full_monitor_work_area
    editor_config = ed.Config()
    editor_config.settings_file = "save/nodes.json"
    # editor_config.navigate_button_index = 2
    addon_params = immapp.AddOnsParams(
        with_node_editor=True,
        with_node_editor_config=editor_config
    )
    immapp.run(params, addon_params)

    print("Stopping preview thread...")
    visa.preview_thread.stop()

if __name__ == "__main__":
    main()