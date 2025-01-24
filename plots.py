import importlib.util
import os
import pickle
from imgui_bundle import imgui, imgui_color_text_edit as te, imgui_fig
from utils import save_file_path
from typing import TYPE_CHECKING, List
import numpy as np

from utils import generate_dock_binary_tree, make_tab_visible
if TYPE_CHECKING:
    from measure import MeasurementData


class Plot():
    def __init__(self, mdata: "MeasurementData"):
        self.data = np.copy(mdata.data)
        self.data_label = mdata.label
        self.data_unit = mdata.unit
        self.data_id = mdata.id
        self.axis = [(a.start, a.end, a.points, a.name, a.unit) for a in mdata.axis]
        self.fig = None
        self.error = None
        self.refresh = False
        self.editor = te.TextEditor()
        self.editor.set_language_definition(te.TextEditor.LanguageDefinition.python())
        if len(self.axis) == 1:
            self.editor.set_text(
f"""import numpy as np
import matplotlib, matplotlib.pyplot as plt
matplotlib.use('Agg') # Remove this when outside nano-measure

# data = np.load("{self.data_label.lower()}.npy", allow_pickle=True).item()

def plot_data(data):
    fig, ax = plt.subplots()
    plt.xlabel(data['axis'][0][3])
    plt.ylabel(data['data_label'])
    ax.plot(np.linspace(*(data['axis'][0][:3])), data['measurement'])
    return fig

# plot_data(data)
""")
        else:
            self.editor.set_text(
f"""import numpy as np
import matplotlib, matplotlib.pyplot as plt
matplotlib.use('Agg') # Remove this when outside nano-measure

# data = np.load("{self.data_label.lower()}.npy", allow_pickle=True).item()

def plot_data(data):
    fig, ax = plt.subplots()
    plt.xlabel(data['axis'][0][3])
    plt.ylabel(data['axis'][1][3])
    ax.imshow(
        data['measurement'], 
        extent=[data['axis'][0][0], data['axis'][0][1], data['axis'][1][0], data['axis'][1][1]],
        cmap='plasma', 
        interpolation='nearest'
    )
    return fig

# plot_data(data)
""")

        self.run_code()
        
    def run_code(self):
        name = f"plot_module{self.data_id}"
        spec = importlib.util.spec_from_loader(name, loader=None)
        try:
            module = importlib.util.module_from_spec(spec)
            exec(self.editor.get_text(), module.__dict__)
            if hasattr(module, "plot_data"):
                try:
                    self.fig = module.plot_data(self.formated_data())
                    self.error = None
                    self.refresh = True
                    # save_plots()
                except Exception as e:
                    print("---Error runnig plot function---")
                    self.error = str(e)
                    print(e)
            else:
                self.error = "No plot_data function found"
        except Exception as e:
            print("---Error loading custom code---")
            self.error = str(e)
            print(e)

    def formated_data(self):
        return {
            "axis": self.axis,
            "measurement": self.data,
            "data_label": self.data_label,
            "data_unit": self.data_unit
        }
    
    def save_numpy(self, path: str):
        _d = self.formated_data()
        np.save(path, _d, allow_pickle=True)

    def save_code(self, path):
        with open(path, "w") as out:
            out.write(self.editor.get_text())

    def make_picklable(self):
        self._bkp_text = self.editor.get_text()
        self.fig = None
        self.editor = None

    def restore(self):
        self.editor = te.TextEditor()
        self.editor.set_language_definition(te.TextEditor.LanguageDefinition.python())
        self.editor.set_text(self._bkp_text)
        del self._bkp_text


plots: List[Plot] = []
leaves = []
size = None
def render_plots(plots_dock_id):
    global leaves
    global size
    _n = len(plots)

    if _n != len(leaves):
        imgui.internal.dock_builder_remove_node(plots_dock_id)
        imgui.internal.dock_builder_add_node(plots_dock_id)

        # No need to split the nodes, I think
        # leaves = generate_dock_binary_tree(plots_dock_id, _n)
        leaves = [_ for _ in range(_n)]
        for i, leaf in enumerate(leaves):
            # imgui.internal.dock_builder_dock_window(f"###Plot{i+1}", leaf)
            imgui.internal.dock_builder_dock_window(f"###Plot{plots[i].data_id}", plots_dock_id)

        imgui.internal.dock_builder_finish(plots_dock_id)

    for i, plot in enumerate(plots):
        imgui.begin(f"{i+1}###Plot{plot.data_id}")
        imgui.begin_horizontal(f"plt{i+1}")
        # imgui.text("Imagina uma imagem do matplotlib aqui")
        imgui.begin_vertical("plot_vert")
        if plot.fig:
            imgui_fig.fig("Plot", plot.fig, size=size, refresh_image=plot.refresh)
            plot.refresh = False
        if plot.error:
            imgui.text_colored(imgui.ImVec4(242/255, 78/255, 78/255, 1), "Error: " + plot.error)
        imgui.end_vertical()
        imgui.begin_vertical(f"plt_code{i+1}")
        plot.editor.render(f"Data {plot.data_label}", a_size=imgui.ImVec2(0, imgui.get_content_region_avail().y - 30))
        imgui.begin_horizontal("buttons")
        if imgui.button("Run", size=imgui.ImVec2(80, 0)):
            plot.run_code()
        if imgui.button("Save this code"):
            path = save_file_path("Save python code", default_path=f"{plot.data_label.lower()}.py")
            if path:
                plot.save_code(path)
        if imgui.button("Save Numpy data"):
            path = save_file_path("Save .npy file", default_path=f"{plot.data_label.lower()}.npy")
            if path:
                plot.save_numpy(path)
        imgui.end_horizontal()
        imgui.end_vertical()
        imgui.end_horizontal()
        imgui.end()

def add_plot(mdata: "MeasurementData"):
    make_tab_visible("Plots")
    make_tab_visible(f"###Plot{mdata.id}")
    if any(p.data_id == mdata.id for p in plots):
        return
    plots.append(Plot(mdata))


# script_dir = os.path.dirname(os.path.abspath(__file__))
# file_path = os.path.join(script_dir, "save", "plots.pkl")
# def save_plots():
#     global plots
#     with open(file_path, "wb") as f:
#         for plot in plots:
#             plot.make_picklable()
#         pickle.dump(plots, f)
#         for plot in plots:
#             plot.restore()

# def load_plots():
#     global plots
#     try:
#         with open(file_path, "rb") as f:
#             plots = pickle.load(f)
#             for plot in plots:
#                 plot.restore()
#                 plot.run_code()
#     except FileNotFoundError:
#         pass