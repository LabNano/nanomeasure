from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore

is_first_frame = True

def gui():
    global is_first_frame
    global nodes
    imgui.separator()
    ed.begin("Node Editor", imgui.ImVec2(0.0, 0.0))


    ed.begin_node(ed.NodeId(1))
    imgui.begin_vertical("node")
    imgui.text("------------------ Node 1 ------------------")
    imgui.begin_horizontal("content")
    imgui.spring(0, 0)
    imgui.begin_vertical("inputs", imgui.ImVec2(0, 0), 0.0)
    imgui.text("Input 1")
    imgui.text("Input 2")
    imgui.text("Input 3")
    imgui.end_vertical()

    imgui.spring(1)

    imgui.begin_vertical("outputs", imgui.ImVec2(0, 0), 1.0)
    imgui.text("Output 1")
    imgui.text("Output 2")
    imgui.text("Output 3")
    imgui.end_vertical()

    imgui.spring(0, 0)

    imgui.end_horizontal()
    imgui.end_vertical()
    ed.end_node()


    if ed.begin_create():
        ed.end_create()

    ed.end()
    is_first_frame = False

def main():
    global nodes
    from imgui_bundle import immapp

    immapp.run(
        gui,
        with_markdown=True,
        with_node_editor=True,
        window_size=(800, 600),
        window_title="Node Editor",
    )

if __name__ == "__main__":
    main()