import math
import time

import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.osrs.power_chopper import OSRSPowerChopper
from utilities.geometry import Point
from utilities.mappings import item_ids as iid
from utilities.mappings import locations as loc
from utilities.walker import Walker, WalkPath
from utilities.color_util import Color
from utilities.sprite_scraper import SpriteScraper, ImageType
import pytweening
from pathlib import Path
from utilities.mappings.colors_rgb import BLUE, BLUE, GREEN, CYAN, YELLOW
import cv2
import pyautogui as pag
import random
import random

class Cooker(OSRSBot):
    def __init__(self):
        bot_title = "Cooker"  # i.e. "<Script Name>"
        description = ("Cook fish")
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 180
        self.options_set = False

        self.walker = Walker(self, dest_square_side_length=10)

        self.bank_color = self.cp.hsv.GREEN_MARK
        self.range_color = self.cp.hsv.PINK_MARK

        self.scrape()


    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Raw karambwan"
        # search_string = "Deposit Inventory"
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

        Lastly, utilize the numerous quality-of-life-improving methods available in the
        `Bot` and `RuneLiteBot` classes. Leveraging these methods significantly
        accelerates the development process.
        """


        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = start_time
        first_run = True

        xp_timestamp = time.time()

        while time.time() - start_time < end_time:
            rk = self.get_karambwan_count()
            self.log_msg(f"Raw karambwans at {rk}")

            if self.get_total_xp() != -1:
                xp_timestamp = time.time()
            if time.time() - xp_timestamp > 300:
                self.log_msg("No XP gain detected for 5 minutes, stopping script.")
                self.logout_and_stop_script("[END]")
                return

            if self.is_run_off() and self.get_run_energy() >= random.randint(10, 60):
                self.toggle_run(state="on")


            if self.is_bank_window_open():
                if first_run:
                    self.sleep()
                    self.open_bank_tab(3)
                    first_run = False
                if self.get_karambwan_count() == 28:
                    pag.press("esc")
                    continue
                else:
                    self.bank_left_click_deposit_all()
                    self.sleep()
                    if rect := self.find_sprite(win=self.win.game_view, png="raw-karambwan-bank.png", folder="items"):
                        self.mouse.move_to(rect.random_point())
                        self.mouse.click()
                        self.sleep()
                        pag.press("esc")
                        self.sleep()
                    else:
                        self.log_msg("could not find raw karambwan in bank.")
                        self.logout_and_stop_script("[END]")
            if self.get_karambwan_count() == 0:
                if not self.move_mouse_to_color_obj(self.bank_color):
                    self.log_msg("Could not find bank booth.")
                    continue
                if not self.get_mouseover_text(contains="Use"):
                    continue
                if not self.mouse.click(check_red_click=True):
                    self.log_msg("Could not click bank booth.")
                    continue
                else:
                    self.sleep_until_bank_open(timeout=8)
            if self.get_karambwan_count() > 0:
                if not self.move_mouse_to_color_obj(self.range_color):
                    self.log_msg("Could not find range.")
                    continue
                if not self.get_mouseover_text(contains="Cook"):
                    continue
                if not self.mouse.click(check_red_click=True):
                    self.log_msg("Could not click range.")
                    continue
                if self.wait_till_interface_text(texts="What"):
                    pag.press("space")
                    while self.get_karambwan_count() > 0:
                        time.sleep(0.5)
                    self.sleep()

                # break chance
                break_time = 0
                if rd.random_chance(0.25):
                    break_time = random.randint(1, 5)
                if rd.random_chance(0.05):
                    break_time = random.randint(5, 30)
                if rd.random_chance(0.01):
                    break_time = random.randint(30, 300)
                if break_time > 5:
                    self.log_msg(f"Taking a break for {break_time} seconds.")
                time.sleep(break_time)
                xp_timestamp += break_time
            
            
            if time.time() - last_update > 300:
                self.update_progress((time.time() - start_time) / end_time)
                last_update = time.time()

            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.logout_and_stop_script("[END]")

    def get_karambwan_count(self) -> int:
        return self.get_num_item_in_inv(png="raw-karambwan.png", folder="items", confidence=0.03)