from pyboy import PyBoy, WindowEvent

class Gameboy:


    def __init__(self, rom, debug=False):
        self.debug = debug
        self.pyboy = self.load_rom(rom)

    def load_rom(self, rom):
        return PyBoy(rom, window_type="SDL2" if self.debug else "headless", window_scale=3, debug=self.debug, game_wrapper=True)

    def dpad_up(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_ARROW_UP)

    def dpad_down(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)

    def dpad_right(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)

    def dpad_left(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)

    def a(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_BUTTON_A)

    def b(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_BUTTON_B)

    def start(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_BUTTON_START)

    def select(self) -> None:
        pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)

    def screenshot(self):
        return pyboy.screen_image()
