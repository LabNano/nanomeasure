from imgui_bundle import imgui, immapp, hello_imgui, imgui_node_editor as ed # type: ignore
import visa
from layout import render_node, render_link, create_links
from classes import ChannelNode, node_classes
import state

is_first_frame = True

def gui():
    global is_first_frame
    dock_id = imgui.get_id("DockSpace")
    imgui.dock_space(dock_id, imgui.ImVec2(0, 0))
    
    if is_first_frame:
        is_first_frame = False
        # imgui.internal.dock_builder_remove_node_child_nodes()

    
    imgui.begin("Node Editor")
    ed.begin("Node Editor")
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
    imgui.end()

    # imgui.begin("Preview")
    # imgui.end()


def main():
    visa.preview_thread = visa.PreviewThread(query_interval_ms=50)
    visa.preview_thread.start()

    for instrument in visa.find_resources():
        state.nodes += [ChannelNode(instrument)]


    params = immapp.SimpleRunnerParams(
        gui,
        window_title="Node Editor",
    ).to_runner_params()
    params.imgui_window_params.enable_viewports = True
    editor_config = ed.Config()
    editor_config.settings_file = ""
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