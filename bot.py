"""
    A bot that interacts with a Mastodon compatible API, plays gameboy games via a Poll
"""

import os
import random
import time

import toml
from mastodon import Mastodon
from requests.exceptions import RequestException

from gb import Gameboy


class Bot:
    """
    A Mastodon-API Compatible bot that handles gameboy gameplay through polls
    """

    def __init__(self, config_path="config.toml"):
        # If config_path is not provided, use the config.toml file in the same
        # directory as the script
        # Get the directory of the current script
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(self.script_dir, "config.toml")
        with open(config_path, "r", encoding="utf-8") as config_file:
            self.config = toml.load(config_file)
            self.mastodon_config = self.config.get("mastodon", {})
            self.gameboy_config = self.config.get("gameboy", {})

        self.mastodon = self.login()
        print(self.gameboy_config.get("rom"))
        rom = os.path.join(self.script_dir, self.gameboy_config.get("rom"))
        self.gameboy = Gameboy(rom, True)

    def simulate(self):
        """Simulates gameboy actions by pressing random buttons, useful for testing"""
        while True:
            # print(self.gameboy.is_running())
            # self.gameboy.random_button()
            buttons = {
                "a": self.gameboy.a,
                "b": self.gameboy.b,
                "start": self.gameboy.start,
                "select": self.gameboy.select,
                "up": self.gameboy.dpad_up,
                "down": self.gameboy.dpad_down,
                "right": self.gameboy.dpad_right,
                "left": self.gameboy.dpad_left,
                "random": self.gameboy.random_button,
                "tick": "tick",
            }
            # self.gameboy.random_button()
            print(buttons)
            press = input("Button: ")
            if press == "tick":
                for _ in range(60):
                    self.gameboy.pyboy.tick()
            else:
                buttons[press]()
                self.gameboy.pyboy.tick()
            # time.sleep(1)

    def random_button(self):
        """Chooses a random button and presses it on the gameboy"""
        buttons = {
            "a": self.gameboy.a,
            "b": self.gameboy.b,
            "start": self.gameboy.start,
            "select": self.gameboy.select,
            "up": self.gameboy.dpad_up,
            "down": self.gameboy.dpad_down,
            "right": self.gameboy.dpad_right,
            "left": self.gameboy.dpad_left,
        }

        random_button = random.choice(list(buttons.keys()))
        action = buttons[random_button]
        action()
        return random_button

    def login(self):
        """Logs into the mastodon server using config credentials"""
        server = self.mastodon_config.get("server")
        print(f"Logging into {server}")
        return Mastodon(
            access_token=self.mastodon_config.get("access_token"), api_base_url=server
        )

    def post_poll(self, status, options, expires_in=60 * 60, reply_id=None):
        """Posts a poll to Mastodon compatible server"""
        poll = self.mastodon.make_poll(
            options, expires_in=expires_in, hide_totals=False
        )
        return self.mastodon.status_post(
            status, in_reply_to_id=reply_id, language="en", poll=poll
        )

    def save_ids(self, post_id, poll_id):
        """Saves post IDs to a text file"""
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.realpath(__file__))
        ids_loc = os.path.join(script_dir, "ids.txt")
        with open(ids_loc, "w", encoding="utf-8") as file:
            file.write(f"{post_id},{poll_id}")

    def read_ids(self):
        """Reads IDs from the text file"""
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.realpath(__file__))
            ids_loc = os.path.join(script_dir, "ids.txt")
            with open(ids_loc, "r", encoding="utf-8") as file:
                content = file.read()
                if content:
                    post_id, poll_id = content.split(",")
                    return post_id, poll_id
        except FileNotFoundError:
            return None, None

        return None

    def pin_posts(self, post_id, poll_id):
        """Pin posts to profile"""
        self.mastodon.status_pin(poll_id)
        self.mastodon.status_pin(post_id)

    def unpin_posts(self, post_id, poll_id):
        """Unpin posts from profile"""
        self.mastodon.status_unpin(post_id)
        self.mastodon.status_unpin(poll_id)

    def take_action(self, result):
        """Presses button on gameboy based on poll result"""
        buttons = {
            "up ⬆️": self.gameboy.dpad_up,
            "down ⬇️": self.gameboy.dpad_down,
            "right ➡️": self.gameboy.dpad_right,
            "left ⬅️": self.gameboy.dpad_left,
            "🅰": self.gameboy.a,
            "🅱": self.gameboy.b,
            "start": self.gameboy.start,
            "select": self.gameboy.select,
        }
        print(buttons)
        # Perform the corresponding action
        if result.lower() in buttons:
            action = buttons[result.lower()]
            action()
        else:
            print(f"No action defined for '{result}'.")

    def retry_mastodon_call(self, func, *args, retries=5, interval=10, **kwargs):
        """Continuously retries mastodon call, useful for servers with timeout issues"""
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                print(f"Failure to execute {func.__name__}: {e}")
                time.sleep(interval)
        return False  # Failed to execute

    def run(self):
        """
        Runs the main gameplay, reads mastodon poll result, takes action, generates new posts
        """
        self.gameboy.load()
        post_id, poll_id = self.read_ids()
        top_result = None

        if post_id:
            try:
                self.unpin_posts(post_id, poll_id)
            except BaseException:
                time.sleep(30)
                self.unpin_posts(post_id, poll_id)

            poll_status = self.mastodon.status(poll_id)
            poll_results = poll_status.poll["options"]
            max_result = max(poll_results, key=lambda x: x["votes_count"])
            if max_result["votes_count"] == 0:
                button = self.random_button()
                top_result = f"Random (no votes, chose {button})"
            else:
                top_result = max_result["title"]
                self.take_action(top_result)

        frames = self.gameboy.loop_until_stopped()
        result = False
        if frames >= 70:
            result = self.gameboy.build_gif("gif_images")
        else:
            gif_dir = os.path.join(self.script_dir, "gif_images")
            self.gameboy.empty_directory(gif_dir)

        image = self.gameboy.screenshot()
        alt_text = 'Screenshot of ' + self.gameboy_config.get('title', 'a Game Boy game.')
        media = self.retry_mastodon_call(
          self.mastodon.media_post, 
          retries=5, 
          interval=10, 
          media_file=image, 
          description=alt_text
        )
        media_ids = []
        # Probably add a check here if generating a gif is enabled (so we don't
        # have to generate one every single hour?)
        try:
            previous_frames = self.gameboy.get_recent_frames("screenshots", 25)
            previous_media = self.retry_mastodon_call(
                self.mastodon.media_post,
                retries=5,
                interval=10,
                media_file=previous_frames,
                description="Video of the previous 45 frames",
            )
            media_ids = [media["id"], previous_media["id"]]
        except BaseException:
            media_ids = [media["id"]]

        post = self.retry_mastodon_call(
            self.mastodon.status_post,
            retries=5,
            interval=10,
            status=(
                f"Previous Action: {top_result}\n\n"
                "#pokemon #gameboy #nintendo #FediPlaysPokemon"
            ),
            media_ids=[media_ids],
        )

        poll = self.retry_mastodon_call(
            self.post_poll,
            retries=5,
            interval=10,
            status="Vote on the next action:\n\n#FediPlaysPokemon",
            options=[
                "Up ⬆️",
                "Down ⬇️",
                "Right ➡️ ",
                "Left ⬅️",
                "🅰",
                "🅱",
                "Start",
                "Select",
            ],
            reply_id=post["id"],
        )

        self.retry_mastodon_call(
            self.pin_posts,
            retries=5,
            interval=10,
            post_id=post["id"],
            poll_id=poll["id"],
        )
        result = False
        if result:
            gif = self.retry_mastodon_call(
                self.mastodon.media_post,
                retries=5,
                interval=10,
                media_file=result,
                description="Video of pokemon gold movement",
            )
            self.retry_mastodon_call(
                self.mastodon.status_post,
                retries=10,
                interval=10,
                status="#Pokemon #FediPlaysPokemon",
                media_ids=[gif["id"]],
                in_reply_to_id=poll["id"],
            )

        self.save_ids(post["id"], poll["id"])

        # Save game state
        self.gameboy.save()

    def test(self):
        """Method used for testing"""
        self.gameboy.load()
        self.gameboy.get_recent_frames("screenshots", 25)
        # self.gameboy.build_gif("gif_images")
        while True:
            inp = input("Action: ")
            buttons = {
                "up": self.gameboy.dpad_up,
                "down": self.gameboy.dpad_down,
                "right": self.gameboy.dpad_right,
                "left": self.gameboy.dpad_left,
                "a": self.gameboy.a,
                "b": self.gameboy.b,
                "start": self.gameboy.start,
                "select": self.gameboy.select,
            }
            # Perform the corresponding action
            if inp.lower() in buttons:
                action = buttons[inp.lower()]
                # self.gameboy.tick()
                action()
                frames = self.gameboy.loop_until_stopped()
                if frames > 51:
                    self.gameboy.build_gif("gif_images")
                else:
                    gif_dir = os.path.join(self.script_dir, "gif_images")
                    self.gameboy.empty_directory(gif_dir)
            else:
                print(f"No action defined for '{inp}'.")
            self.gameboy.save()
            # self.gameboy.build_gif("gif_images")
            # self.take_action(inp)
            # self.gameboy.tick(300)


if __name__ == "__main__":
    bot = Bot()
    # bot.test()
    bot.run()
    # for i in range(2):
    #    bot.run()
    #    time.sleep(60)
    # bot.simulate()
