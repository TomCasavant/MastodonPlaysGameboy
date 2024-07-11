"""
    A bot that interacts with a Mastodon compatible API, plays Game Boy games via a poll
"""

import os
import random
import time

import toml
from mastodon import Mastodon
from requests.exceptions import RequestException

from gb import GameBoy


script_dir = os.path.dirname(os.path.realpath(__file__))
ids_loc = os.path.join(script_dir, "ids.txt")
gif_dir = os.path.join(script_dir, "gif_images")

class Bot:
    """
    A Mastodon-API compatible bot that handles Game Boy gameplay through polls
    """

    def __init__(self, config_path="config.toml"):
        # If config_path is not provided, use the config.toml file in the same
        # directory as the script
        config_path = os.path.join(script_dir, "config.toml")
        with open(config_path, "r", encoding="utf-8") as config_file:
            self.config = toml.load(config_file)
            self.mastodon_config = self.config.get("mastodon", {})
            self.game_boy_config = self.config.get("gameboy", {})

        self.mastodon = self.login()
        print(self.game_boy_config.get("rom"))
        rom = os.path.join(script_dir, self.game_boy_config.get("rom"))
        self.game_boy = GameBoy(rom, True)

    def simulate(self):
        """Simulates Game Boy actions by pressing random buttons, useful for testing"""
        while True:
            # print(self.game_boy.is_running())
            # self.game_boy.random_button()
            buttons = {
                "a": self.game_boy.a,
                "b": self.game_boy.b,
                "start": self.game_boy.start,
                "select": self.game_boy.select,
                "up": self.game_boy.dpad_up,
                "down": self.game_boy.dpad_down,
                "right": self.game_boy.dpad_right,
                "left": self.game_boy.dpad_left,
                "random": self.game_boy.random_button,
                "tick": "tick",
            }
            # self.game_boy.random_button()
            print(buttons)
            press = input("Button: ")
            if press == "tick":
                for _ in range(60):
                    self.game_boy.pyboy.tick()
            else:
                buttons[press]()
                self.game_boy.pyboy.tick()
            # time.sleep(1)

    def login(self):
        """Logs into the Mastodon server using config credentials"""
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
        with open(ids_loc, "w", encoding="utf-8") as file:
            file.write(f"{post_id},{poll_id}")

    def read_ids(self):
        """Reads IDs from the text file"""
        try:
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
        """Presses button on Game Boy based on poll result"""
        buttons = {
            "Up ⬆️": self.game_boy.dpad_up,
            "Down ⬇️": self.game_boy.dpad_down,
            "Right ➡️": self.game_boy.dpad_right,
            "Left ⬅️": self.game_boy.dpad_left,
            "🅰": self.game_boy.a,
            "🅱": self.game_boy.b,
            "Start": self.game_boy.start,
            "Select": self.game_boy.select,
        }
        print(buttons)
        # Perform the corresponding action
        if result in buttons:
            action = buttons[result]
            action()
            return result
        elif result == "random":
            random_button = random.choice(list(buttons.keys()))
            action = buttons[random_button]
            action()
            return random_button
        else:
            print(f"No action defined for '{result}'.")
            return "INVALID BUTTON"

    def retry_mastodon_call(self, func, *args, retries=5, interval=10, **kwargs):
        """Continuously retries Mastodon call, useful for servers with timeout issues"""
        for _ in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Failure to execute {func.__name__}: {e}")
                time.sleep(interval)
        return False  # Failed to execute

    def run(self):
        """
        Runs the main gameplay, reads Mastodon poll result, takes action, generates new posts
        """
        self.game_boy.load()
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
            max_votes = max(map(lambda x: x["votes_count"], poll_results))
            if max_votes == 0:
                random_button = self.take_action("random")
                top_result = f"Random (no votes, chose {random_button})"
            else:
                top_results = [x for x in poll_results if x["votes_count"] == max_votes]
                if len(top_results) > 1:
                    top_result = random.choice(top_results)["title"]
                    self.take_action(top_result)
                    top_result = f"Random (tie vote, chose {top_result})"
                else:
                    top_result = top_results[0]["title"]
                    self.take_action(top_result)

        frames = self.game_boy.loop_until_stopped()
        result = False
        if frames >= 70:
            result = self.game_boy.build_gif("gif_images", self.game_boy_config['gif_outline'])
        else:
            self.game_boy.empty_directory(gif_dir)

        image = self.game_boy.screenshot()
        alt_text = 'Screenshot of ' + self.game_boy_config.get('title', 'a Game Boy game.')
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
            previous_frames = self.game_boy.get_recent_frames("screenshots",
                25,
                self.game_boy_config['gif_outline']
            )
            previous_media = self.retry_mastodon_call(
                self.mastodon.media_post,
                retries=5,
                interval=10,
                media_file=previous_frames,
                description="Video of the previous 45 frames",
            )
            media_ids = [media["id"], previous_media["id"]]
        except BaseException as e:
            print(f"ERROR {e}")
            media_ids = [media["id"]]

        post = self.retry_mastodon_call(
            self.mastodon.status_post,
            retries=5,
            interval=10,
            status=(
                f"Previous Action: {top_result}\n\n"
                "#Pokemon #GameBoy #Nintendo #FediPlaysPokemon"
            ),
            media_ids=[media_ids],
        )

        poll_duration = self.mastodon_config.get('poll_duration', 60)

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
            expires_in=poll_duration*60,
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
                description="Video of Pokémon Gold movement",
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
        self.game_boy.save()

    def test(self):
        """Method used for testing"""
        self.game_boy.load()
        self.game_boy.get_recent_frames("screenshots", 25)
        # self.game_boy.build_gif("gif_images")
        while True:
            inp = input("Action: ")
            buttons = {
                "up": self.game_boy.dpad_up,
                "down": self.game_boy.dpad_down,
                "right": self.game_boy.dpad_right,
                "left": self.game_boy.dpad_left,
                "a": self.game_boy.a,
                "b": self.game_boy.b,
                "start": self.game_boy.start,
                "select": self.game_boy.select,
            }
            # Perform the corresponding action
            if inp in buttons:
                action = buttons[inp]
                # self.game_boy.tick()
                action()
                frames = self.game_boy.loop_until_stopped()
                if frames > 51:
                    self.game_boy.build_gif("gif_images")
                else:
                    self.game_boy.empty_directory(gif_dir)
            else:
                print(f"No action defined for '{inp}'.")
            self.game_boy.save()
            # self.game_boy.build_gif("gif_images")
            # self.take_action(inp)
            # self.game_boy.tick(300)


if __name__ == "__main__":
    bot = Bot()
    # bot.test()
    bot.run()
    # for i in range(2):
    #    bot.run()
    #    time.sleep(60)
    # bot.simulate()
