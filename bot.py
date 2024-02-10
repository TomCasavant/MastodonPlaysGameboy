from gb import Gameboy
import random
import time
from mastodon import Mastodon
import toml
import os

class Bot:

    def __init__(self, config_path="config.toml"):
        # If config_path is not provided, use the config.toml file in the same directory as the script
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        config_path = os.path.join(script_dir, "config.toml")
        with open(config_path, 'r') as config_file:
            self.config = toml.load(config_file)
            self.mastodon_config = self.config.get('mastodon', {})
            self.gameboy_config = self.config.get('gameboy', {})

        self.mastodon = self.login()
        print(self.gameboy_config.get('rom'))
        rom = os.path.join(script_dir, self.gameboy_config.get('rom'))
        self.gameboy = Gameboy(rom, False)

    def simulate(self):
        while True:
            #print(self.gameboy.is_running())
            if True:
                #self.gameboy.random_button()
                buttons = {
                 "a" : self.gameboy.a,
                 "b" : self.gameboy.b,
                 "start" : self.gameboy.start,
                 "select" : self.gameboy.select,
                 "up" : self.gameboy.dpad_up,
                 "down" : self.gameboy.dpad_down,
                 "right" : self.gameboy.dpad_right,
                 "left" : self.gameboy.dpad_left,
                 "random" : self.gameboy.random_button,
                 "tick" : "tick"
                }
                #self.gameboy.random_button()
                print(buttons)
                press = input("Button: ")
                if press == "tick":
                    for i in range(60):
                        self.gameboy.pyboy.tick()
                else:
                    buttons[press]()
                    self.gameboy.pyboy.tick()
                #time.sleep(1)

    def login(self):
        server = self.mastodon_config.get('server')
        print(f"Logging into {server}")
        return Mastodon(access_token=self.mastodon_config.get('access_token'), api_base_url=server)

    def post_poll(self, status, options, expires_in=30*60, reply_id=None):
        poll = self.mastodon.make_poll(options, expires_in=expires_in, hide_totals=False)
        return self.mastodon.status_post(status, in_reply_to_id=reply_id, language='en', poll=poll)

    def save_ids(self, post_id, poll_id):
        script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        ids_loc = os.path.join(script_dir, "ids.txt")
        with open(ids_loc, 'w') as file:
            file.write(f"{post_id},{poll_id}")

    def read_ids(self):
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
            ids_loc = os.path.join(script_dir, "ids.txt")
            with open(ids_loc, 'r') as file:
                content = file.read()
                if content:
                    post_id, poll_id = content.split(',')
                    return post_id, poll_id
        except FileNotFoundError:
            return None, None

    def pin_posts(self, post_id, poll_id):
        self.mastodon.status_pin(poll_id)
        self.mastodon.status_pin(post_id)

    def unpin_posts(self, post_id, poll_id):
        self.mastodon.status_unpin(post_id)
        self.mastodon.status_unpin(poll_id)

    def take_action(self, result):
        buttons = {
            "up ⬆️": self.gameboy.dpad_up,
            "down ⬇️": self.gameboy.dpad_down,
            "right ➡️": self.gameboy.dpad_right,
            "left ⬅️": self.gameboy.dpad_left,
            "🅰": self.gameboy.a,
            "🅱": self.gameboy.b,
            "start": self.gameboy.start,
            "select": self.gameboy.select
        }

        # Perform the corresponding action
        if result.lower() in buttons:
            action = buttons[result.lower()]
            action()
        else:
            print(f"No action defined for '{result}'.")

    def run(self):
        self.gameboy.load()
        post_id, poll_id = self.read_ids()
        top_result = None

        if post_id:
            try:
                self.unpin_posts(post_id, poll_id)
            except:
                time.sleep(30)
                self.unpin_posts(post_id, poll_id)

            poll_status = self.mastodon.status(poll_id)
            poll_results = poll_status.poll['options']
            max_result = max(poll_results, key=lambda x: x['votes_count'])
            if (max_result['votes_count'] == 0):
                self.gameboy.random_button()
            else:
                top_result = max_result['title']
                self.take_action(top_result)

        self.gameboy.tick(300) # Progress the screen to the next position
        image = self.gameboy.screenshot()
        try:
            media = self.mastodon.media_post(image, description='Image of pokemon rom')
        except:
            time.sleep(45)
            media = self.mastodon.media_post(image, description='Image of pokemon rom')

        time.sleep(50)
        try:
            post = self.mastodon.status_post(f"(Test) The highest voted result was {top_result}", media_ids=[media['id']])
        except:
            time.sleep(30)
            post = self.mastodon.status_post(f"(Test) The highest voted result was {top_result}", media_ids=[media['id']])

        try:
            poll = self.post_poll("Pick one of the options:", ["Up ⬆️", "Down ⬇️", "Right ➡️ ", "Left ⬅️", "🅰", "🅱", "Start", "Select"], reply_id=post['id'])
        except:
            time.sleep(30)
            poll = self.post_poll("Pick one of the options:", ["Up ⬆️", "Down ⬇️", "Right ➡️ ", "Left ⬅️", "🅰", "🅱", "Start", "Select"], reply_id=post['id'])

        try:
            self.pin_posts(post['id'], poll['id'])
        except:
            time.sleep(30)
            self.pin_posts(post['id'], poll['id'])

        self.save_ids(post['id'], poll['id'])

        # Save game state
        self.gameboy.save()

if __name__ == '__main__':
    bot = Bot()
    bot.run()
    # for i in range(2):
    #    bot.run()
    #    time.sleep(60)
    #bot.simulate()

