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

class PlankMaker(OSRSBot):
    def __init__(self):
        bot_title = "Plank Maker"  # i.e. "<Script Name>"
        description = ("Make planks from ")
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 120
        self.options_set = False

        self.walker = Walker(self, dest_square_side_length=10)

        self.bank_tile = Point(1592, 3476)
        self.buy_tile = Point(1624, 3500)

        self.sawmill_op_color = self.cp.hsv.CYAN_MARK
        self.bank_color = self.cp.hsv.GREEN_MARK

        self.scrape()


    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Teak logs, Teak plank"
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
        while time.time() - start_time < end_time:
            if self.is_run_off() and self.get_run_energy() >= random.randint(10, 60):
                self.toggle_run(state="on")

            if self.is_bank_window_open():
                if self.is_item_in_inv(png="teak-plank.png", folder="items"):
                    i = self.get_first_item_index(png="teak-plank.png", folder="items")
                    self.mouse.move_to(self.win.inventory_slots[i].random_point())
                    self.mouse.click()
                    self.sleep()
                if rect := self.find_sprite(win=self.win.game_view, png="teak-logs-bank.png", folder="items"):
                    self.mouse.move_to(rect.random_point())
                    self.mouse.click()
                    time.sleep(.3)
                else:
                    self.open_bank_tab(4)
                    self.sleep()
                self.sleep()
                pag.press("esc")
                self.sleep()
            elif self.is_item_in_inv(png="teak-logs.png", folder="items"):
                if not self.find_colors(rect=self.win.game_view, colors=self.sawmill_op_color):
                    self.travel_to(
                        tile_coord=self.buy_tile,
                        walk_path=None,
                        dest_name="wc_guild_bank_to_sawmill",
                    )
                if rect := self.find_colors(rect=self.win.game_view, colors=self.sawmill_op_color):
                    rect = rect[0]
                    self.mouse.move_to(rect.random_point())
                    if self.get_mouseover_text(contains="Buy"):
                        if self.mouse.click(check_red_click=True):
                            self.wait_till_interface_text(texts="How")
                        self.sleep()
                if self.check_interface_text(texts="How"):
                    pag.press("3")
                    time.sleep(.6)
                self.sleep()
            else:
                if rect := self.find_colors(rect=self.win.game_view, colors=self.bank_color):
                    rect = rect[0]
                    self.mouse.move_to(rect.random_point())
                    if self.get_mouseover_text(contains="Use"):
                        if self.mouse.click(check_red_click=True):
                            for _ in range(10):
                                if self.is_bank_window_open():
                                    break
                                time.sleep(1)
                        self.sleep()
                else:
                    self.travel_to(
                        tile_coord=self.bank_tile,
                        walk_path=None,
                        dest_name="sawmill_to_wc_guild_bank",
                    )
            
            if time.time() - last_update > 300:
                self.update_progress((time.time() - start_time) / end_time)
                last_update = time.time()

            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.stop()

    def travel_to(self, tile_coord: Point, walk_path: WalkPath, dest_name: str):
        self.log_msg(f"Traveling to {dest_name}...")
        if self.walker.travel_to_dest_along_path(
            tile_coord,
            walk_path,
            dest_name,
        ):
            self.log_msg(f"Arrived: {dest_name}")
        else:
            self.log_msg(f"Failed to arrive at {dest_name}.")
        while self.is_traveling():
            self.sleep()
