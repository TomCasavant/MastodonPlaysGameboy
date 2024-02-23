from pyboy import PyBoy, WindowEvent
import random
import threading
import os
import re
import shutil
from PIL import Image, ImageDraw
from moviepy.editor import ImageSequenceClip
import numpy as np

class Gameboy:

    def __init__(self, rom, debug=False):
        self.debug = debug
        self.rom = rom
        self.running = False
        self.pyboy = self.load_rom(self.rom)
        self.pyboy.set_emulation_speed(0)

    def start_thread(self):
        self.pyboy = self.load_rom(self.rom)
        self.pyboy.set_emulation_speed(1)
        print(self.pyboy)
        #self.run()

    def is_running(self):
        return self.running

    def run(self) -> None:
        self.running = True
        while True:
            self.random_button()

    def tick(self, ticks=1, gif=True):
        for tick in range(ticks):
            if gif:
                self.screenshot("gif_images")
            self.pyboy.tick()

    def compare_frames(self, frame1, frame2):
        arr1 = np.array(frame1)
        arr2 = np.array(frame2)

        diff = np.abs(arr1 - arr2)
        changed_pixels = np.count_nonzero(diff)
        percent = (changed_pixels / diff.size) * 100
        print(f"Pixels: {changed_pixels} {percent}%")
        return percent

    def empty_directory(self, directory):
        image_files = [i for i in os.listdir(directory) if os.path.isfile(os.path.join(directory, i))]
        for img in image_files:
            os.remove(os.path.join(directory, img))

    def build_gif(self, image_path, delete=True, fps=120):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        gif_dir = os.path.join(script_dir, image_path)
        image_files = [i for i in os.listdir(gif_dir) if os.path.isfile(os.path.join(gif_dir, i))]
        #image_files.sort()
        image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
        images = []
        print(len(image_files))
        #image1 = Image.open(os.path.join(gif_dir, image_files[30])).convert('L')
        #diffs = []
        for file in image_files:
            #diffs.append(self.compare_frames(image1, Image.open(os.path.join(gif_dir, file)).convert('L')))
            gameboy_outline = Image.open('gameboy.png').convert("RGB")
            img = Image.open(os.path.join(gif_dir, file)).convert("RGB")
            img = img.resize((181, 163))
            combined = gameboy_outline.copy()
            combined.paste(img, (165, 151))
            combined.save(os.path.join(gif_dir, file))
            images.append(os.path.join(gif_dir, file))
            #with Image.open(os.path.join(gif_dir, file)) as img:
            #    images.append(img.copy())
            #if delete:
            #    os.remove(os.path.join(gif_dir, file))

        if images:
            save_path = None
            #diffs = diffs[30:]
            #if max(diffs) > 10:
            duration = int(1000/fps)
                #freeze_frames = [images[-1]] * int(1000/duration) # Freeze on last frame
                # print(len(freeze_frames))
                #print(f"Duration {duration}")
            #frames = [images[0]]*350 + images
            frames = images
            save_path = os.path.join(script_dir, "action.mp4")
            clip = ImageSequenceClip(frames, fps=fps)
            clip.write_videofile(save_path, codec='libx264')
            if delete:
                for img in images:
                    os.remove(img)
            #images[0].save(save_path, save_all=True, append_images=images[1:]+freeze_frames, interlace=False, loop=0, duration=duration, disposal=1)           
            return save_path

        return False

    def stop(self):
        self.running = False

    def load_rom(self, rom):
        return PyBoy(rom, window_type="SDL2" if self.debug else "headless", window_scale=3, debug=False, game_wrapper=True)

    def dpad_up(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
        self.tick(4)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
        #print(self.pyboy.stop())
        #self.tick()

    def dpad_down(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        print("down")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
        #self.tick()

    def dpad_right(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_RIGHT)
        print("right")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_RIGHT)
        #self.tick()

    def dpad_left(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_ARROW_LEFT)
        print("left")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_ARROW_LEFT)
        #self.tick()

    def a(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        print("a")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)
        #self.tick()

    def b(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_B)
        print("b")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_B)
        #self.tick()

    def start(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_START)
        print("start")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_START)
        #self.tick()

    def select(self) -> None:
        self.pyboy.send_input(WindowEvent.PRESS_BUTTON_SELECT)
        print("select")
        self.tick(3)
        self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_SELECT)

    def screenshot(self, path='screenshots'):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        screenshot_dir = os.path.join(script_dir, path)
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

    def loop_until_stopped(self, threshold=1):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        running = True
        previous_frame = None
        current_frame = None
        count = 0
        no_movement = 0
        while running:
            previous_frame = current_frame
            self.tick(30)
            count+=5
            current_frame = Image.open(os.path.join(script_dir, "screenshot.png")).convert('L')
            if previous_frame:
                diff = self.compare_frames(previous_frame, current_frame)
                print(f"Frame {count}: {diff}")
                if (diff < threshold):
                    no_movement += 1
                else:
                    no_movement = 0
            if no_movement > 5:
                running = False
            if count > 1000: # Shouldn't have lasted this long, something has gone wrong
                print("Error")
                return 0
        return count
