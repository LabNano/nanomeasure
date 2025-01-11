from imgui_bundle import imgui, immapp, hello_imgui, imgui_node_editor as ed # type: ignore
import visa
from layout import render_node, render_link, create_links
from classes import ChannelNode, node_classes
from measure import is_measuring, compliance, info
import state

is_first_frame = True

def gui():
    global is_first_frame
    dock_id = imgui.get_id("DockSpace")
    imgui.dock_space(dock_id, imgui.ImVec2(0, 0))
    
    if is_first_frame:
        is_first_frame = False
        imgui.internal.dock_builder_remove_node(dock_id)
        imgui.internal.dock_builder_add_node(dock_id)
        imgui.internal.dock_builder_set_node_size(dock_id, imgui.get_main_viewport().size)

        imgui.spacing()
        ids = imgui.internal.dock_builder_split_node(dock_id, imgui.Dir.right, 0.25)
        imgui.internal.dock_builder_dock_window("Node Editor", ids.id_at_opposite_dir)
        imgui.internal.dock_builder_dock_window("Info", ids.id_at_dir)

        imgui.internal.dock_builder_finish(dock_id)
    
    imgui.begin("Node Editor")
    ed.begin("Node Editor")
    for node in state.nodes:
        render_node(node)

    render_link()
    if not is_measuring:
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
                    state.save_state()
            imgui.end_popup()
        ed.resume()

    if is_first_frame:
        ed.navigate_to_content(0.0)

    ed.end()
    imgui.end()

    imgui.begin("Info")
    imgui.begin_vertical("info", size=imgui.ImVec2(imgui.get_content_region_avail().x, imgui.get_content_region_avail().y))
    imgui.spring(0)
    
    info()
    imgui.spring(1)
    errors = compliance()
    imgui.spring(0, 20)



    if not errors:
        imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(103/255, 153/255, 103/255, 1))
        imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(89/255, 133/255, 90/255, 1))
        imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(69/255, 105/255, 70/255, 1))
    else:
        imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(105/255, 105/255, 105/255, 1))
        imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(90/255, 90/255, 90/255, 1))
        imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(75/255, 75/255, 75/255, 1))
    imgui.button("Measure", imgui.ImVec2(imgui.get_content_region_avail().x, 50))
    imgui.pop_style_color()
    imgui.pop_style_color()
    imgui.pop_style_color()
    imgui.end_vertical()

    imgui.end()


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
    params.app_window_params.window_geometry.full_screen_mode = hello_imgui.FullScreenMode.full_monitor_work_area
    editor_config = ed.Config()
    editor_config.settings_file = "save/nodes.json"
    # editor_config.navigate_button_index = 2
    addon_params = immapp.AddOnsParams(
        with_node_editor=True,
        with_node_editor_config=editor_config
    )
    immapp.run(params, addon_params)


    # immapp.run(
    #     gui,
    #     # with_markdown=True,
    #     with_node_editor=True,
    #     # window_size=(800, 600),
    #     window_title="Node Editor",
    # )

    print("Stopping preview thread...")
    visa.preview_thread.stop()

if __name__ == "__main__":
    main()