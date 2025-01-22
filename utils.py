from imgui_bundle import portable_file_dialogs as pfd

def open_file_path(title = "NanoMeasure Open File"):
    p = pfd.open_file(title)
    return p.result()

def save_file_path(title = "NanoMeasure Save File", default_path = None):
    p = pfd.save_file(title, default_path)
    return p.result()
