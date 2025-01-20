import threading
from imgui_bundle import imgui
from classes import WriteRangeNode, WriteConstantNode, Node, Pin, MeasurementNode, ChannelNode, HeatmapNode, PlotNode
import numpy as np
import time
from typing import cast, List, Mapping
import state
import visa

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
        if n and len(pin.connections) > n:
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
            enforce_connections(node, node.outputs[0], 0, 1)
            writing = 0
            for c in node.outputs[0].connections:
                if isinstance(c[0], WriteRangeNode):
                    writing += 1
                if writing > 1:
                    if render:
                        imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                        imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                        imgui.text_colored(imgui.color_convert_u32_to_float4(node.outputs[0].color), node.outputs[0].name)
                        imgui.text("cannot connect to multiple scan nodes")
                        imgui.end_horizontal()
                    errors += 1
        
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
                reading = 0
                for c in o.connections:
                    if isinstance(c[0], WriteRangeNode) or isinstance(c[0], WriteConstantNode):
                        writing += 1
                    elif isinstance(c[0], MeasurementNode):
                        reading += 1
                if writing > 1:
                    if render:
                        imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                        imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                        imgui.text_colored(imgui.color_convert_u32_to_float4(o.color), o.name)
                        imgui.text("cannot be written to by more than one node")
                        imgui.end_horizontal()
                    errors += 1
                if writing and reading:
                    if render:
                        imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                        imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                        imgui.text_colored(imgui.color_convert_u32_to_float4(o.color), o.name)
                        imgui.text("cannot be set to write and read at the same time")
                        imgui.end_horizontal()
                    errors += 1
                    
    if not measurements:
        if render:
            imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
            imgui.text("You must have at least one")
            imgui.text_colored(imgui.color_convert_u32_to_float4(MeasurementNode.color), "measurement node")
            imgui.end_horizontal()
        errors += 1

    if scans:
        if not without_inputs:
            if render:
                imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text("You must have at least one scan without an input loop")
                imgui.end_horizontal()
            errors += 1
        if without_inputs > 1:
            if render:
                imgui.begin_horizontal(f"complianceerror{errors}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text("You cannot have more than one scan without an input loop")
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
                imgui.begin_horizontal(f"channels{node.id}.{c[0].id}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text_colored(imgui.color_convert_u32_to_float4(c[0].outputs[c[1]].color), c[0].instrument.channels[c[1]][0])
                imgui.spring(0, 4)
                imgui.text("at")
                imgui.spring(0, 4)
                imgui.text_colored(imgui.color_convert_u32_to_float4(c[0].color), c[0].instrument.name)
                imgui.spring(0, 4)
                imgui.text(f"from {node.start_value:.2e} to {node.end_value:.2e} in {node.points} points")
                imgui.end_horizontal()
        if isinstance(node, WriteConstantNode) and node.inputs[0].connections:
            if node.inputs[0].connections:
                c = list(node.inputs[0].connections)[0]
                imgui.text_wrapped(f"{c[0].instrument.channels[c[1]][0]} at {c[0].instrument.name} to constant {node.value:.2e}")
                # imgui.text_wrapped(f"{c[0].instrument.channels[c[1]][0]} at {c[0].instrument.name} to constant {node.value:.2e}")
    
    connected_pins = [pin for node in state.nodes for pin in node.outputs if isinstance(node, ChannelNode) if pin.connections]
    imgui.separator_text(f"Reading {len(connected_pins)} channel{'s' if len(connected_pins) != 1 else ''}")
    
    for node in state.nodes:
        if isinstance(node, ChannelNode):
            channels = [pin for pin in node.outputs if pin.connections]
            if channels:
                imgui.begin_horizontal(f"readchannels{node.id}", size=imgui.ImVec2(imgui.get_content_region_avail().x, 0))
                imgui.text_colored(imgui.color_convert_u32_to_float4(node.color), node.title)
                imgui.spring(0, 4)
                imgui.text(f"on channel{"s" if len(channels) != 1 else ""}")
                imgui.spring(0, 4)
                for i, c in enumerate(channels):
                    imgui.text_colored(imgui.color_convert_u32_to_float4(c.color), c.name + (", " if i < len(channels) - 1 else ""))
                    imgui.spring(0, 0)
                imgui.end_horizontal()
        
    
    imgui.end_vertical()

def make_tab_visible(name: str):
    window = imgui.internal.find_window_by_name(name)
    if not window or not window.dock_node or not window.dock_node.tab_bar:
        return
    window.dock_node.tab_bar.next_selected_tab_id = window.tab_id

def render_preview():
    imgui.begin_vertical("info", size=imgui.ImVec2(imgui.get_content_region_avail().x, imgui.get_content_region_avail().y))
    imgui.spring(0)
    
    info()
    imgui.spring(1)
    errors = compliance()
    imgui.spring(0, 20)



    if not errors and not is_measuring:
        imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(103/255, 153/255, 103/255, 1))
        imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(89/255, 133/255, 90/255, 1))
        imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(69/255, 105/255, 70/255, 1))
    else:
        imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(105/255, 105/255, 105/255, 1))
        imgui.push_style_color(imgui.Col_.button_hovered, imgui.ImVec4(90/255, 90/255, 90/255, 1))
        imgui.push_style_color(imgui.Col_.button_active, imgui.ImVec4(75/255, 75/255, 75/255, 1))
    if imgui.button("Measuring..." if is_measuring else "Measure", imgui.ImVec2(imgui.get_content_region_avail().x, 50)):
        if is_measuring:
            stop_measure()
        elif not errors:
            start_measure()
    imgui.pop_style_color()
    imgui.pop_style_color()
    imgui.pop_style_color()
    imgui.end_vertical()


class MeasurementAxis:
    def __init__(self, start, end, points):
        self.start = start
        self.end = end
        self.points = points

class MeasurementData:
    axis: List[MeasurementAxis]
    current: List[int]
    data: np.ndarray

    def __init__(self, axis: List[MeasurementAxis]):
        self.axis = axis
        self.current = [0] * len(axis)
        self.data = np.full(tuple(a.points for a in self.axis), np.nan, dtype=np.float32)


measurement_thread = None
measurement_data: Mapping[int, MeasurementData] = {}
def start_measure():
    global measurement_thread
    visa.disable_preview()
    imgui.set_window_focus("Measure")
    measurement_thread = MeasurementThread()
    measurement_thread.start()

def stop_measure():
    global measurement_thread
    if measurement_thread:
        measurement_thread.stop()
        make_tab_visible("Measurement Info")
        imgui.set_window_focus("Node Editor")
        measurement_thread = None

def get_first_scan_node():
        for node in state.nodes:
            if isinstance(node, WriteRangeNode) and not list(node.inputs[1].connections):
                return node

class MeasurementThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.keep_running = True


    def run(self):
        global is_measuring
        is_measuring = True
        print("Starting measurement")

        for node in state.nodes:
            if isinstance(node, MeasurementNode):
                s = []
                for i in node.inputs[:-1]:
                    if isinstance(list(i.connections)[0][0], WriteRangeNode):
                        n = list(i.connections)[0][0]
                        a = MeasurementAxis(n.start_value, n.end_value, n.points)
                        s.append(a)
                measurement_data[node.id] = MeasurementData(s)


        initial_scan = get_first_scan_node()
        def scan_node(node: WriteRangeNode, axis = 0):
            for c in node.outputs[0].connections:
                if isinstance(c[0], MeasurementNode):
                    m = measurement_data[c[0].id]
                    if m.current == [0 for i in range(len(m.axis))]:
                        m.data = np.full(tuple(a.points for a in m.axis), np.nan, dtype=np.float32)

            for i in range(node.points):
                if not self.keep_running:
                    return

                #Set Data
                channel = list(node.inputs[0].connections)[0]
                try:
                    value = node.start_value + i * (node.end_value - node.start_value) / (node.points-1)
                    # print("Setting data: ", channel[0].outputs[channel[1]].name, value)
                    cast(ChannelNode, channel[0]).instrument.channels[channel[1]][3](cast(ChannelNode, channel[0]).instrument.resource, value)
                    time.sleep(node.step_time)
                except Exception as e:
                    print("Error setting data: ", e)
                    pass
                for c in node.outputs[0].connections:
                    if not self.keep_running:
                        return
                    if isinstance(c[0], MeasurementNode):
                        #Read Data
                        m = measurement_data[c[0].id]
                        # m.current[axis] = i
                        m.current[c[1]] = i
                        if np.isnan(m.data[tuple(m.current)]):
                            channel = list(c[0].inputs[-1].connections)[0]
                            #This line reads the data if the data is not already present
                            # print("Reading data: ",channel[0].outputs[channel[1]].name ,tuple(m.current))
                            try:
                                m.data[tuple(m.current)] = cast(ChannelNode, channel[0]).instrument.channels[channel[1]][2](cast(ChannelNode, channel[0]).instrument.resource)
                            except Exception as e:
                                print("Error measuring data: ", e)
                for c in node.outputs[0].connections:
                    if isinstance(c[0], WriteRangeNode):
                        scan_node(c[0], axis + 1)
            # Reset current to 0 on this loop before goin back to previous

            for c in node.outputs[0].connections:
                if isinstance(c[0], MeasurementNode):
                    m = measurement_data[c[0].id]
                    m.current[c[1]] = 0
  
  
        for node in state.nodes:
            if isinstance(node, WriteConstantNode):
                channel = list(node.inputs[0].connections)[0]
                value = node.value
                print("Setting data: ", channel[0].outputs[channel[1]].name, value)
                cast(ChannelNode, channel[0]).instrument.channels[channel[1]][3](cast(ChannelNode, channel[0]).instrument.resource, value)
  
        scan_node(initial_scan)
                        
        is_measuring = False
        if self.keep_running:
            print("Measurement finished")

    def stop(self):
        self.keep_running = False
        self.join()
        print("Measurement interrupted")