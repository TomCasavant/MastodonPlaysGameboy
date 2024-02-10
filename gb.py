from pyboy import PyBoy, WindowEvent
import random
import threading
import os
import re
import shutil

class Gameboy:

    def __init__(self, rom, debug=False):
        self.debug = debug
        self.rom = rom
        self.running = False
        self.pyboy = self.load_rom(self.rom)
        self.pyboy.set_emulation_speed(0)

    def start_thread(self):
        self.pyboy = self.load_rom(self.rom)
        self.pyboy.set_emulation_speed(0)
        print(self.pyboy)
        #self.run()

    def is_running(self):
        return self.running

    def run(self) -> None:
        self.running = True
        while True:
            self.random_button()

    def tick(self, ticks=1):
        for tick in range(ticks):
            self.pyboy.tick()

    def stop(self):
        self.running = False

    def load_rom(self, rom):
        return PyBoy(rom, window_type="SDL2" if self.debug else "headless", window_scale=3, debug=False, game_wrapper=True)

    def dpad_up(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
        #print(self.pyboy.stop())
        #self.tick()

    def dpad_down(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        print("down")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
        #self.tick()

    def dpad_right(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
        print("right")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
        #self.tick()

    def dpad_left(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
        print("left")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
        #self.tick()

    def a(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        print("a")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
        #self.tick()

    def b(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
        print("b")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
        #self.tick()

    def start(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_START)
        print("start")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_START)
        #self.tick()

    def select(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)
        print("select")
        self.tick()
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_SELECT)

    def screenshot(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        screenshot_dir = os.path.join(script_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)  # Create screenshots directory if it doesn't exist

        # Get existing screenshot numbers
        screenshot_numbers = [int(re.search(r'screenshot_(\d+)\.png', filename).group(1)) for filename in os.listdir(screenshot_dir) if re.match(r'screenshot_\d+\.png', filename)]
        next_number = max(screenshot_numbers, default=0) + 1

        # Save the screenshot with the next available number
        screenshot_path = os.path.join(screenshot_dir, f'screenshot_{next_number}.png')
        screenshot_path_full = os.path.join(script_dir, 'screenshot.png')
        self.pyboy.screen_image().save(screenshot_path_full)
        shutil.copyfile(screenshot_path_full, screenshot_path)  # Copy the screenshot to the screenshots directory
        return screenshot_path_full

    def random_button(self):
        button = random.choice([self.dpad_up, self.dpad_down, self.dpad_right, self.dpad_left, self.a, self.b, self.start, self.select])
        button()

    def load(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        save_loc = os.path.join(script_dir, "save.state")
        if os.path.exists(save_loc):
            with open(save_loc, "rb") as file:
                self.pyboy.load_state(file)
            return True
        else:
            print("Save state does not exist")
            return False

    def save(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        save_loc = os.path.join(script_dir, "save.state")

        with open(save_loc, "wb") as file:
            self.pyboy.save_state(file)

