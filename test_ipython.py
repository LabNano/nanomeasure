from imgui_bundle import imgui, immapp, hello_imgui
from IPython.terminal.prompts import Prompts, Token
from IPython import start_ipython
from traitlets.config.loader import Config
import threading

class AppWithIpython:
    def __init__(self):
        self.runner_params = hello_imgui.RunnerParams()
        self.runner_params.callbacks.show_gui = self.gui
        self.click_count = 0
        self._stop_event = threading.Event()

    def gui(self):
        imgui.text(f"Button clicked {self.click_count} times")
        if imgui.button("Click me"):
            self.click_count += 1


    def run_ipython(self):
        banner = "Nano Measure GUI mode\nAccess GUI with 'app' variable\nType 'exit()' to quit\n"
        
        class ClassicPrompt(Prompts):
            def in_prompt_tokens(self):
                return [(Token.Prompt, '>>> ')]
            def continuation_prompt_tokens(self, width=None):
                return [(Token.Prompt, '... ')]

        c = Config()
        c.TerminalInteractiveShell.prompts_class = ClassicPrompt
        c.TerminalInteractiveShell.separate_in = ''
        c.TerminalInteractiveShell.banner1 = banner
        
        start_ipython(argv=[], user_ns={'app': self}, config=c)
        self.runner_params.app_shall_exit = True

    def run(self):
        ipython_thread = threading.Thread(target=self.run_ipython, daemon=True)
        ipython_thread.start()
        
        
        try:
            immapp.run(self.runner_params)
        except KeyboardInterrupt:
            self.runner_params.app_shall_exit = True
            pass

if __name__ == "__main__":
    app = AppWithIpython()
    app.run()