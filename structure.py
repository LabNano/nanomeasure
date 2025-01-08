from imgui_bundle import imgui, imgui_node_editor as ed # type: ignore
from typing import List, Tuple
import numpy as np
import visa


class IdProvider:
    _next_id: int = 1
    def next_id(self):
        r = self._next_id
        self._next_id += 1
        return r
    def reset(self):
        self._next_id = 1
ID = IdProvider()

class Type:
    name:str


class ReadableChannel(Type):
    color = imgui.IM_COL32(255, 255, 255, 255)
    name = "Channel"
    pass

class WritableChannel(ReadableChannel):
    color = imgui.IM_COL32(255, 255, 255, 255)
    pass

class Node:
    inputs: List[Tuple[str, type]] = []
    outputs: List[Tuple[str, type]] = []
    id: int
    title: str
    color = imgui.IM_COL32(255, 255, 255, 255)
    def __init__(self):
        self.id = ID.next_id()

    def drawExtras(self):
        pass


class ChannelNode(Node):
    title = "Channel Node"
    color = imgui.IM_COL32(91, 148, 240, 255)
    def __init__(self, instrument: visa.Instrument):
        self.instrument = instrument
        self.title = instrument.name
        self.outputs = [(c[0], WriteNode | MeasurementNode) for c in  instrument.channels]
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

class WriteNode(Node):
    title = "Write Node"

class WriteRangeNode(Node):
    title = "Write Range"

class MeasurementNode(Node):
    pass

class HeatmapNode(MeasurementNode):
    title = "Heatmap Node"

class PlotNode(MeasurementNode):
    title = "Plot Node"

    
ChannelNode.outputs = [("Channel", WriteNode | MeasurementNode)]
ChannelNode.inputs = [("Test", WriteNode | MeasurementNode)]
WriteNode.inputs = [("Channel", ChannelNode), ("Clock", WriteNode)]
WriteNode.outputs = [("Clock", MeasurementNode | WriteNode)]
HeatmapNode.inputs = [("X", ChannelNode), ("Y", ChannelNode), ("Z", ChannelNode)]
PlotNode.inputs = [("X", ChannelNode), ("Y", ChannelNode)]