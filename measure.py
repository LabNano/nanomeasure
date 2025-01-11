import state
from imgui_bundle import imgui
from classes import WriteRangeNode, WriteConstantNode, Node, Pin, MeasurementNode, ChannelNode

is_measuring = False

def get_info():
    pass

def compliance(render = True) -> int:
    scans = []
    consts = []
    measurements = 0
    without_inputs = 0
    errors = 0

    def enforce_connections(node: Node, pin: Pin, n = 1, type = 0, required = True):
        nonlocal errors
        _error = ""
        if required and not len(pin.connections):
            _error = "must have a connection"
        if len(pin.connections) > n:
            _error = f"cannot have more than {n} connection{'s' if n > 1 else ''}"
        if _error:
            if render:
                imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                imgui.text(["input", "output"][type])
                imgui.text_colored(imgui.color_convert_u32_to_float4(pin.color), pin.name)
                imgui.text(_error)
                imgui.end_horizontal()
            errors += 1
        
    if render:
        n = compliance(render = False)
        if n:
            imgui.separator_text(f"Errors: {n}")

    for node in state.nodes:
        if isinstance(node, WriteRangeNode):
            scans.append(node)
            if not len(node.inputs[1].connections):
                without_inputs += 1
            enforce_connections(node, node.inputs[0])
            enforce_connections(node, node.outputs[0], 1, 1)
        
        if isinstance(node, WriteConstantNode):
            consts.append(node)
            enforce_connections(node, node.inputs[0])

        if isinstance(node, MeasurementNode):
            for i in node.inputs:
                enforce_connections(node, i)
            for o in node.outputs:
                enforce_connections(node, i, 1, 1)
            measurements += 1

        if isinstance(node, ChannelNode):
            for o in node.outputs:
                writing = 0
                for c in o.connections:
                    if isinstance(c[0], WriteRangeNode) or isinstance(c[0], WriteConstantNode):
                        writing += 1
                    if writing > 1:
                        if render:
                            imgui.begin_horizontal(f"complianceerror{errors}")
                            imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                            imgui.text_colored(imgui.color_convert_u32_to_float4(o.color), o.name)
                            imgui.text("cannot be written to by more than one node")
                            imgui.end_horizontal()
                        errors += 1
    if not measurements:
        if render:
            imgui.begin_horizontal(f"complianceerror{errors}")
            imgui.text("You must have at least one")
            imgui.text_colored(imgui.color_convert_u32_to_float4(MeasurementNode.color), "measurement node")
            imgui.end_horizontal()
        errors += 1

    if scans:
        if not without_inputs:
            if render:
                imgui.begin_horizontal(f"complianceerror{errors}")
                imgui.text("You must have at least one scan without an input clock")
                imgui.end_horizontal()
            errors += 1
    # else:
    #     if render:
    #         imgui.begin_horizontal(f"complianceerror{errors}")
    #         imgui.text("You must have at least one scan node")
    #         imgui.end_horizontal()
    #     errors += 1

    return errors


def info():
    imgui.begin_vertical("info")
    n = len(list(node for node in state.nodes if (isinstance(node, WriteRangeNode) or isinstance(node, WriteConstantNode)) and node.inputs[0].connections))
    imgui.separator_text(f"Setting {n} channel{'s' if n != 1 else ''}")

    for node in state.nodes:
        if isinstance(node, WriteRangeNode) and node.inputs[0].connections:
            if node.inputs[0].connections:
                c = list(node.inputs[0].connections)[0]
                # imgui.text_wrapped(f"{c[0].instrument.channels[c[1]][0]} at {c[0].instrument.name} from {node.start_value:.2e} to {node.end_value:.2e} in {node.points} points")
                imgui.begin_horizontal(f"channels{c[0].id}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text_colored(imgui.color_convert_u32_to_float4(c[0].outputs[c[1]].color), c[0].instrument.channels[c[1]][0])
                imgui.text("at")
                imgui.text_colored(imgui.color_convert_u32_to_float4(c[0].color), c[0].instrument.name)
                imgui.text(f"from {node.start_value:.2e} to {node.end_value:.2e} in {node.points} points")
                imgui.end_horizontal()
        if isinstance(node, WriteConstantNode) and node.inputs[0].connections:
            if node.inputs[0].connections:
                c = list(node.inputs[0].connections)[0]
                imgui.text_wrapped(f"{c[0].instrument.channels[c[1]][0]} at {c[0].instrument.name} to constant {node.value:.2e}")
                # imgui.text_wrapped(f"{c[0].instrument.channels[c[1]][0]} at {c[0].instrument.name} to constant {node.value:.2e}")
    imgui.end_vertical()