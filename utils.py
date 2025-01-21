import wx
from imgui_bundle import portable_file_dialogs as pfd


def open_file_path():
    p = pfd.open_file("NanoMeasure Open File")
    return p.result()

def save_file_path():
    p = pfd.save_file("NanoMeasure Save File")
    return p.result()

# def get_file_path(wildcard):
#     app = wx.App(None)
#     style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
#     dialog = wx.FileDialog(None, 'Open', wildcard=wildcard, style=style)
#     if dialog.ShowModal() == wx.ID_OK:
#         path = dialog.GetPath()
#     else:
#         path = None
#     dialog.Destroy()
#     return path