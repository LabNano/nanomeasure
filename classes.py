from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List, Tuple, Set, TYPE_CHECKING
import numpy as np
import visa

if TYPE_CHECKING:
    from layout import NodeLayout

class IdProvider:
    _next_id: int = 1
    def next_id(self):
        r = self._next_id
        self._next_id += 1
        return r
    def reset(self):
        self._next_id = 1
ID = IdProvider()

class Pin:
    name:str
    color = imgui.IM_COL32(255, 255, 255, 255)
    connections: Set[Tuple['Node', int]]

    def __init__(self, name = None, color = None):
        if name:
            self.name = name
        if color:
            self.color = color
        self.connections = set()
        pass

class ReadableChannel(Pin):
    color = imgui.IM_COL32(91, 148, 240, 255)
    name = "Channel"

class WritableChannel(ReadableChannel):
    color = imgui.IM_COL32(255, 151, 107, 255)

class Clock(Pin):
    color = imgui.IM_COL32(164, 111, 199, 255)
    name = "Clock"


class Node:
    inputs: List[Pin] = []
    outputs: List[Pin] = []
    id: int
    title: str
    color = imgui.IM_COL32(120, 120, 120, 255)
    def __init__(self):
        self.id = ID.next_id()

    def content(self, layout: "NodeLayout"):
        for i,_ in enumerate(self.inputs):
            layout.add_input(i)
        for o,_ in enumerate(self.outputs):
            layout.add_output(o)
        layout.add_content(self.drawExtras)

    def on_connect(self, pin: int, kind: ed.PinKind):
        pass

    def drawExtras(self):
        pass


class ChannelNode(Node):
    title = "Channel Node"
    color = imgui.IM_COL32(91, 148, 240, 255)
    def __init__(self, instrument: visa.Instrument):
        self.instrument = instrument
        self.title = instrument.name
        self.outputs = [WritableChannel(c[0]) if c[3] else ReadableChannel(c[0]) for c in  instrument.channels]
        super().__init__()

    def drawExtras(self):
        imgui.begin_horizontal("prev")
        _, self.instrument.preview = imgui.checkbox("Preview", self.instrument.preview)
        imgui.push_item_width(100)
        changed, self.instrument.preview_channel = imgui.combo("##channel", self.instrument.preview_channel, [c[0] for c in self.instrument.channels])
        imgui.pop_item_width()
        imgui.end_horizontal()
        if changed:
            self.instrument.preview_buffer.clear()
        if self.instrument.preview:
            imgui.plot_lines("", 
                             np.array(self.instrument.preview_buffer, np.float32), 
                             0, 
                             f"{(0 if len(self.instrument.preview_buffer) == 0 else self.instrument.preview_buffer[-1]):.4e} {self.instrument.channels[self.instrument.preview_channel][1]}", 
                             0 if len(self.instrument.preview_buffer) == 0 else np.min(self.instrument.preview_buffer), 
                             0 if len(self.instrument.preview_buffer) == 0 else np.max(self.instrument.preview_buffer), 
                             imgui.ImVec2(300, 60))

class WriteConstantNode(Node):
    title = "Write Constant"

    def __init__(self):
        self.inputs = [WritableChannel()]
        self.value = 0
        super().__init__()

    def content(self, layout):
        layout.add_input(0)
        conns = list(self.inputs[0].connections)
        if conns:
            self.inputs[0].name = conns[0][0].outputs[conns[0][1]].name
        else:
            self.inputs[0].name = "Channel"
        def _():
            imgui.push_item_width(50)
            imgui.input_float("##value", 0)
            if conns and isinstance(conns[0][0], ChannelNode):
                imgui.same_line(0, 5)
                imgui.text(conns[0][0].instrument.channels[conns[0][1]][1])
            imgui.pop_item_width()
        layout.add_content(_)

class WriteRangeNode(Node):
    color = imgui.IM_COL32(148, 111, 199, 255)
    title = "Write Range"

    def __init__(self):
        self.inputs = [WritableChannel(), Clock("Loop")]
        self.outputs = [Clock()]
        self.start_value = 0.0
        self.end_value = 0.0
        self.step = 0.0
        self.points = 1
        self.startwait = 0.0
        self.step_time = 0.0
        self.clock_type = 0
        super().__init__()

    def content(self, layout):
        _conn = list(self.inputs[0].connections)
        conn = list(self.inputs[1].connections)
        layout.add_input(0)
        layout.add_output(0)
        if _conn and isinstance(_conn[0][0], ChannelNode):
            self.outputs[0].name = _conn[0][0].instrument.short_name + " " + _conn[0][0].outputs[_conn[0][1]].name
        else:
            self.outputs[0].name = "Value"
        def _():
            imgui.push_item_width(50)

            imgui.spacing()
            imgui.spacing()

            imgui.begin_horizontal("range")
            imgui.spring(1)
            imgui.push_id("start")
            imgui.begin_vertical("start", imgui.ImVec2(0, 0), 1.0)

            imgui.begin_horizontal("start")
            imgui.spring(1)
            imgui.text("Start")
            sv_changed, self.start_value = imgui.input_float("##a", self.start_value)
            imgui.end_horizontal()
            
            if self.clock_type == 1:
                stp_changed, sw_changed = (False, False)
            else:
                imgui.begin_horizontal("step")
                imgui.spring(1)
                imgui.text("Step")
                stp_changed, self.step = imgui.input_float("##c", self.step)
                imgui.end_horizontal()

                imgui.begin_horizontal("startwait")
                imgui.spring(1)
                imgui.text("Start Wait")
                sw_changed, self.startwait = imgui.input_float("##e", self.startwait)
                imgui.end_horizontal()
            imgui.end_vertical()
            imgui.pop_id()

            imgui.spring(1)

            imgui.push_id("end")
            imgui.begin_vertical("end", imgui.ImVec2(0, 0), 1.0)

            imgui.begin_horizontal("end")
            imgui.spring(1)
            imgui.text("End")
            ev_changed, self.end_value = imgui.input_float("##b", self.end_value)
            imgui.end_horizontal()

            if self.clock_type == 1:
                pnt_changed, st_changed, = False, False
            else:
                imgui.begin_horizontal("points")
                imgui.spring(1)
                imgui.text("Points")
                pnt_changed, self.points = imgui.input_int("##d", self.points, 0)
                imgui.end_horizontal()

                imgui.begin_horizontal("stept")
                imgui.spring(1)
                imgui.text("Step Time")
                st_changed, self.step_time = imgui.input_float("##f", self.step_time)
                imgui.end_horizontal()
            imgui.end_vertical()
            imgui.pop_id()
            imgui.end_horizontal()
            imgui.pop_item_width()
            imgui.spacing()
            imgui.spacing()

            if self.points < 1:
                self.points = 1
            if self.step_time < 0:
                self.step_time = 0
            if self.step < 0:
                self.step = 0
            if self.startwait < 0:
                self.startwait = 0
            if (sv_changed or ev_changed) and self.step:
                self.points = int((self.end_value - self.start_value) // self.step) + 1
                self.step = (self.end_value - self.start_value) / self.points
            if stp_changed and self.step:
                self.points = int((self.end_value - self.start_value) // self.step) + 1
                self.end_value = self.start_value + self.step * (self.points - 1)
            if pnt_changed and self.points:
                if self.points > 1:
                    self.step = (self.end_value - self.start_value) / (self.points - 1)
            if sv_changed or ev_changed or st_changed or stp_changed or pnt_changed or sw_changed:
                import state
                state.save_state()

        layout.add_content(_)
        layout.add_input(1)
        def _():
            if conn:
                imgui.push_item_width(100)
                _, self.clock_type = imgui.combo("##type", self.clock_type, ["Scan", "Sync"])
                imgui.pop_item_width()
        layout.add_content(_)

class MeasurementNode(Node):
    color = imgui.IM_COL32(106, 145, 81, 255)
    pass

class HeatmapNode(MeasurementNode):
    title = "Heatmap"

    def __init__(self):
        self.inputs = [Clock("X"), Clock("Y"), ReadableChannel("Z")]
        super().__init__()

class PlotNode(MeasurementNode):
    title = "Plot"

    def __init__(self):
        self.inputs = [Clock("X"), ReadableChannel("Y")]
        super().__init__()


node_classes = [WriteConstantNode, WriteRangeNode, HeatmapNode, PlotNode]