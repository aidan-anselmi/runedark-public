import math
import time
from typing import List

import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.osrs.power_chopper import OSRSPowerChopper
from utilities.geometry import Point, RuneLiteObject
from utilities.mappings import item_ids as iid
from utilities.mappings import locations as loc
from utilities.travel_step import StepType
from utilities.walker import Walker, WalkPath
from utilities.color_util import Color
from utilities.sprite_scraper import SpriteScraper, ImageType
import pytweening
from pathlib import Path
from utilities.mappings.colors_rgb import BLUE, BLUE, GREEN, CYAN, YELLOW
import cv2
import pyautogui as pag
import random
from utilities.travel import *


class SaltMiner(OSRSBot):
    def __init__(self):
        bot_title = "Exhibit A"
        description = (
            "This example is here to highlight how bots can be further organized by"
            " folders while still being dynamically picked up by the `options_builder`."
        )
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 120
        self.options_set = False
        self.scrape()

    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Basalt"
        image_type = ImageType.ALL
        destination = dest_dir

        self.path = scraper.search_and_download(
            search_string=search_string,
            image_type=image_type,
            destination=destination,)
        return 

    def create_options(self):
        """Add bot options.

        Use an `OptionsBuilder` to define the options for the bot. For each function
        call below, we define the type of option we want to create, its key, a label
        for the option that the user will see, and the possible values the user can
        select. The key is used in the `save_options` method to unpack the dictionary
        of options after the user has selected them.
        """
        self.options_builder.add_slider_option(
            "run_time", "How long to run (minutes)?", 1, 500
        )
        self.options_builder.add_text_edit_option(
            "text_edit_example", "Text Edit Example", "Placeholder text here"
        )
        self.options_builder.add_checkbox_option(
            "multi_select_example", "Multi-select Example", ["A", "B", "C"]
        )
        self.options_builder.add_dropdown_option(
            "menu_example", "Menu Example", ["A", "B", "C"]
        )

    def save_options(self, options: dict):
        """Load options into the bot object.

        For each option in the dictionary, if it is an expected option, save the value
        as a property of the bot. If any unexpected options are found, log a warning.
        If an option is missing, set the `options_set` flag to False.
        """
        for option in options:
            if option == "run_time":
                self.run_time = options[option]
            elif option == "text_edit_example":
                self.log_msg(f"Text edit example: {options[option]}")
            elif option == "multi_select_example":
                self.log_msg(f"Multi-select example: {options[option]}")
            elif option == "menu_example":
                self.log_msg(f"Menu example: {options[option]}")
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Options are packed incorrectly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.run_time} minutes.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        """Execute the main logic loop of the bot.

        Responsibilities:
            1. To halt the bot within this function, call `self.stop()`. This action is
                usually necessary when the bot encounters errors or gets stuck.

            2. Call `self.update_progress()` at least once per gameplay loop. Also,
                use `self.log_msg()` frequently to update the bot controller on the
                current status and intended behavior of the bot.

            3. After the main loop execution, remember to call `self.stop()` to
                terminate the daemon thread (`BotThread`) and prevent it from
                unintentionally running in the background.

        Lastly, utilize the numerous quality-of-life-improving methods available in
        `Bot` and `RuneLiteBot` classes. Leveraging these methods significantly
        accelerates the development process.
        """
        self.walker = Walker(self, dest_square_side_length=4)
        self.traveler = Traveler(self, self.walker)
        self.to_noter_steps = [StairsStep(Point(2838, 10336), Point(2845, 10351), "Up mine stairs", "Climb", extra_wait_time=2.5),]
        self.return_to_mine_steps = [
            StairsStep(Point(2872, 3935), Point(2867, 3938), "Down mine stairs", "Descend", extra_wait_time=2.5),
            WalkStep(Point(2845, 10351), Point(2838, 10336), "Walk to mine"),
        ]

        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        self.start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = self.start_time

        self.action_win = self.win.current_action
        self.action_win.top += 58
        self.action_win.height += 3

        self.salt_1_color = self.cp.hsv.CYAN_MARK
        self.salt_2_color = self.cp.hsv.PINK_MARK
        self.salt_3_color = self.cp.hsv.YELLOW_MARK
        self.salt_4_color = self.cp.hsv.GREEN_MARK
        self.snowflake_color = self.cp.hsv.CYAN_MARK

        self.consec_no_mine_checks = 0

        while time.time() - self.start_time < end_time:
            # update progress
            if time.time() - last_update > 300:
                self.update_progress((time.time() - self.start_time) / end_time)
                last_update = time.time()

            if self.is_inv_full():
                self.note_basalt()

            if not self.is_player_doing_action("Mining", rect=self.action_win) and not self.strayed_far():
                if not self.mine_salt():
                    self.consec_no_mine_checks += 1
                else:
                    self.consec_no_mine_checks = 0

                if self.consec_no_mine_checks > 5:
                    self.traveler.travel(self.return_to_mine_steps)
            else:
                self.log_msg("Strayed far, returning to mine.")
                self.traveler.travel(self.return_to_mine_steps)                    

            # check for no xp gain
            if self.has_not_gained_xp(duration=300):
                self.log_msg("No XP gained for 5 minutes, returning to bank")
                self.logout_and_stop_script()
                return
            
            self.toggle_run_on_if_enough_energy()
            time.sleep(.5)

        self.update_progress(1)
        self.log_msg("[END]")
        self.stop()

    def strayed_far(self) -> bool:
        cur_location = self.traveler.get_cur_location()
        if cur_location == Point(-1, -1):
            return False
        return math.dist(cur_location, Point(2838, 10336)) > 25

    def mine_salt(self) -> bool:
        # 1/3 chance to mine each salt type
        salt_choice = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        if salt_choice < 2:
            salt_color = self.salt_1_color
        elif salt_choice < 5:
            salt_color = self.salt_2_color
        elif salt_choice < 8:
            salt_color = self.salt_3_color
        else:
            salt_color = self.salt_4_color
        for _ in range(5):
            if self.move_mouse_to_color_obj(salt_color):
                if res := self.mouse.click(check_red_click=True):
                    if random.random() < 0.2:
                        self.sleep()
                        res = self.move_mouse_to_color_obj(salt_color) and self.mouse.click(check_red_click=True)
                    time.sleep(.5)
                    self.sleep_while_color_moving(salt_color)
                    return res
            else:
                self.log_msg("Could not find salt to mine.")
        return False
    
    def note_basalt(self) -> bool:
        if not self.traveler.travel(self.to_noter_steps):
            self.log_msg("Failed to travel to noter.")
            return False

        basalt_rect = self.find_sprite(win=self.win.game_view, png="basalt.png", folder="items")
        snowflake_rect = self.find_colors(self.win.game_view, colors=self.snowflake_color)
        if basalt_rect and snowflake_rect:
            snowflake_rect = snowflake_rect[0]

            self.mouse.move_to(basalt_rect.random_point())
            if not self.get_mouseover_text(contains="Use"):
                self.log_msg("Could not get basalt mouseover text.")
                return False
            self.sleep()
            self.mouse.click()
            self.sleep()
            self.mouse.move_to(snowflake_rect.random_point())
            if not self.get_mouseover_text(contains="Use") and not self.mouse.click(check_red_click=True):
                self.log_msg("Could not get snowflake mouseover text.")
                return False
            self.sleep()

        if not self.traveler.travel(self.return_to_mine_steps):
            self.log_msg("Failed to travel to noter.")
            return False

        self.log_msg("Noted basalt.")
        return True