from imgui_bundle import imgui
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

    def drawExtras(self):
        pass


class ChannelNode(Node):
    title = "Channel Node"
    color = imgui.IM_COL32(91, 148, 240, 255)
    def __init__(self, instrument: visa.Instrument):
        self.instrument = instrument
        self.title = instrument.name
        self.outputs = [WritableChannel(c[0]) if c[3] else ReadableChannel(c[0]) for c in  instrument.channels]
        visa.preview_thread.add_instrument(instrument)
        super().__init__()

    def drawExtras(self):
        imgui.begin_horizontal("prev")
        _, self.instrument.preview = imgui.checkbox("Preview", self.instrument.preview)
        imgui.push_item_width(100)
        changed, self.instrument.preview_channel = imgui.combo("", self.instrument.preview_channel, [c[0] for c in self.instrument.channels])
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

class WriteRangeNode(Node):
    color = imgui.IM_COL32(148, 111, 199, 255)
    title = "Write Range"

    def content(self, layout):
        layout.add_input(0)
        layout.add_output(0)
        def _():
            imgui.checkbox("Test", True)
        layout.add_content(_)
        layout.add_input(1)

class MeasurementNode(Node):
    color = imgui.IM_COL32(106, 145, 81, 255)
    pass

class HeatmapNode(MeasurementNode):
    title = "Heatmap Node"

class PlotNode(MeasurementNode):
    title = "Plot Node"

    
ChannelNode.outputs = [ReadableChannel()]
ChannelNode.inputs = [ReadableChannel()]
WriteConstantNode.inputs = [WritableChannel()]
WriteRangeNode.inputs = [WritableChannel(), Clock()]
WriteRangeNode.outputs = [Clock()]
HeatmapNode.inputs = [Clock(), ReadableChannel("X"), ReadableChannel("Y"), ReadableChannel("Z")]
PlotNode.inputs = [Clock(), ReadableChannel("X"), ReadableChannel("Y")]


node_classes = [WriteConstantNode, WriteRangeNode, HeatmapNode, PlotNode]