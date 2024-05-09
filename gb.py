"""
    Convenient class to interface with PyBoy
"""

import os
import random
import re
import shutil

import numpy as np
from moviepy.editor import ImageSequenceClip
from PIL import Image
from pyboy import PyBoy, WindowEvent


class Gameboy:
    """Provides an easy way to interface with pyboy

    Args:
        rom (str): A string pointing to a rom file (MUST be GB or GBC, no GBA files)
        debug (bool, optional): Enable debug mode. Defaults to false
    """

    def __init__(self, rom, debug=False):
        self.debug = debug
        self.rom = rom
        self.running = False
        self.pyboy = self.load_rom(self.rom)
        self.pyboy.set_emulation_speed(0)

    def is_running(self):
        """Returns True if bot is running in constant loop mode, false otherwise"""
        return self.running

    def run(self) -> None:
        """Continuously loop while pressing random buttons on the gameboy"""
        self.running = True
        while True:
            self.random_button()

    def tick(self, ticks=1, gif=True):
        """Advances the gameboy by a specified number of frames.

        Args:
            ticks (int, optional): The number of frames to advance. Defaults to 1
            gif (bool, optional): Generates screenshots for the gif if True
        """
        for _ in range(ticks):
            if gif:
                self.screenshot("gif_images")
            self.pyboy.tick()

    def compare_frames(self, frame1, frame2):
        """
        Compares two frames from gameboy screenshot, returns a percentage difference between the two
        """
        arr1 = np.array(frame1)
        arr2 = np.array(frame2)

        diff = np.abs(arr1 - arr2)
        changed_pixels = np.count_nonzero(diff)
        percent = (changed_pixels / diff.size) * 100
        print(f"Pixels: {changed_pixels} {percent}%")
        return percent

    def get_recent_frames(self, directory, num_frames=100, gif_outline='gameboy.png'):
        """Gets the most recent frames from a provided directory"""
        script_dir = os.path.dirname(os.path.realpath(__file__))
        screenshot_dir = os.path.join(script_dir, directory)
        # Probably should replace this with heap (especially since there are so
        # many image files)
        image_files = [
            os.path.join(screenshot_dir, i) for i in os.listdir(screenshot_dir)
        ]
        image_files.sort(key=os.path.getmtime)
        latest = image_files[-(num_frames):]

        count = 0
        for image in latest:
            print(image)
            count += 1
            shutil.copy(image, os.path.join(script_dir, "tmp", f"{count}.png"))

        self.build_gif(os.path.join(script_dir, "tmp"),
            fps=5,
            output_name="test.mp4",
            gif_outline=gif_outline
        )
        self.empty_directory(os.path.join(script_dir, "tmp"))
        return os.path.join(script_dir, "test.mp4")

    def empty_directory(self, directory):
        """Deletes all images in the provided directory"""
        image_files = [
            i
            for i in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, i))
        ]
        for img in image_files:
            os.remove(os.path.join(directory, img))

    def build_gif(self, image_path, delete=True, fps=120, output_name="action.mp4", gif_outline="gameboy.png"):
        """Build a gif from a folder of images"""
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        gif_dir = os.path.join(script_dir, image_path)
        image_files = [
            i for i in os.listdir(gif_dir) if os.path.isfile(os.path.join(gif_dir, i))
        ]
        # image_files.sort()
        image_files.sort(key=lambda x: int("".join(filter(str.isdigit, x))))
        images = []
        print(len(image_files))
        for file in image_files:

            gameboy_outline = Image.open(
                os.path.join(script_dir, gif_outline)
            ).convert("RGB")
            img = Image.open(os.path.join(gif_dir, file)).convert("RGB")
            img = img.resize((822, 733))
            combined = gameboy_outline.copy()
            combined.paste(img, (370, 319)) #370, 319 1192, 1052    
            combined.save(os.path.join(gif_dir, file))
            images.append(os.path.join(gif_dir, file))

        if images:
            save_path = None
            frames = images
            save_path = os.path.join(script_dir, output_name)
            clip = ImageSequenceClip(frames, fps=fps)
            clip.write_videofile(save_path, codec="libx264")
            if delete:
                for img in images:
                    os.remove(img)
            return save_path

        return False

    def stop(self):
        """Stops the continuous gameboy loop"""
        self.running = False

    def load_rom(self, rom):
        """Loads the rom into a pyboy object"""
        return PyBoy(
            rom,
            window_type="SDL2" if self.debug else "headless",
            window_scale=3,
            debug=False,
            game_wrapper=True,
        )

    def dpad_up(self) -> None:
        """Presses up on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
        self.tick(4)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)

    def dpad_down(self) -> None:
        """Presses down on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        print("down")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
        # self.tick()

    def dpad_right(self) -> None:
        """Presses right on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
        print("right")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
        # self.tick()

    def dpad_left(self) -> None:
        """Presses left on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
        print("left")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
        # self.tick()

    def a(self) -> None:
        """Presses a on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        print("a")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
        # self.tick()

    def b(self) -> None:
        """Presses b on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
        print("b")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
        # self.tick()

    def start(self) -> None:
        """Presses start on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_START)
        print("start")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_START)
        # self.tick()

    def select(self) -> None:
        """Presses select on the gameboy"""
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)
        print("select")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_SELECT)

    def screenshot(self, path="screenshots"):
        """Takes a screenshot of gameboy screen and saves it to the path"""
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        screenshot_dir = os.path.join(script_dir, path)
        # Create screenshots directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)

        # Get existing screenshot numbers
        screenshot_numbers = [
            int(re.search(r"screenshot_(\d+)\.png", filename).group(1))
            for filename in os.listdir(screenshot_dir)
            if re.match(r"screenshot_\d+\.png", filename)
        ]
        next_number = max(screenshot_numbers, default=0) + 1

        # Save the screenshot with the next available number
        screenshot_path = os.path.join(screenshot_dir, f"screenshot_{next_number}.png")
        screenshot_path_full = os.path.join(script_dir, "screenshot.png")
        self.pyboy.screen_image().save(screenshot_path_full)
        # Copy the screenshot to the screenshots directory
        shutil.copyfile(screenshot_path_full, screenshot_path)
        return screenshot_path_full

    def random_button(self):
        """Picks a random button and presses it on the gameboy"""
        button = random.choice(
            [
                self.dpad_up,
                self.dpad_down,
                self.dpad_right,
                self.dpad_left,
                self.a,
                self.b,
                self.start,
                self.select,
            ]
        )
        button()

    def load(self, state):
        """Loads the save state"""
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        save_loc = os.path.join(script_dir, state)
        result = False
        if os.path.exists(save_loc):
            with open(save_loc, "rb") as file:
                self.pyboy.load_state(file)
            result = True
        else:
            print("Save state does not exist")
        return result

    def save(self, state):
        """Saves current state to a file"""
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        save_loc = os.path.join(script_dir, state)

        with open(save_loc, "wb") as file:
            self.pyboy.save_state(file)

    def loop_until_stopped(self, threshold=1):
        """Simulates the gameboy bot"""
        script_dir = os.path.dirname(os.path.realpath(__file__))
        running = True
        previous_frame = None
        current_frame = None
        count = 0
        no_movement = 0
        while running:
            previous_frame = current_frame
            self.tick(30)
            count += 5
            current_frame = Image.open(
                os.path.join(script_dir, "screenshot.png")
            ).convert("L")
            if previous_frame:
                diff = self.compare_frames(previous_frame, current_frame)
                print(f"Frame {count}: {diff}")
                if diff < threshold:
                    no_movement += 1
                else:
                    no_movement = 0
            if no_movement > 3:
                running = False
            if (
                count > 1000
            ):  # Shouldn't have lasted this long, something has gone wrong
                print("Error")
                return 0
        return count
