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

class SlayerMelee(OSRSBot):
    def __init__(self):
        bot_title = "Slayer Melee"  # i.e. "<Script Name>"
        description = ("Melee slayer")
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 180
        self.options_set = False

        self.walker = Walker(self, dest_square_side_length=10)

        self.monster_color = self.cp.hsv.CYAN_MARK

        self.scrape()


    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Cooked karambwan, Ring of dueling"
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
        xp_timestamp = time.time()

        self.toggle_auto_retaliate(state="on")
        self.sleep()
        pag.press("f2")  # open combat tab

        while time.time() - start_time < end_time:
            if self.get_total_xp() != -1:
                xp_timestamp = time.time()
            if time.time() - xp_timestamp > 300:
                self.log_msg("No XP gain detected for 5 minutes, stopping script.")
                self.logout_and_stop_script("[END]")
                return

            # heal
            if self.get_hp() != -1:
                while self.get_hp() <= 65 and self.eat_food():
                    self.sleep()
                if self.get_hp() <= 40:
                    self.log_msg("HP low after eating, returning to banks")
                    self.return_to_bank()

            # loot
            while self.pickup_ground_item():
                self.sleep()
                while self.high_alch_item():
                    self.sleep()
                if self.is_inv_full():
                    self.eat_food()
                if self.full_trip():
                    self.log_msg("Inventory full, returning to bank")
                    self.return_to_bank()

            # fight 
            if self.has_no_hp_bar():
                self.atack_monster()

            # update progress
            if time.time() - last_update > 300:
                self.update_progress((time.time() - start_time) / end_time)
                last_update = time.time()

        self.update_progress(1)
        self.log_msg("[END]")
        self.logout_and_stop_script("[END]")

    def eat_food(self) -> bool:
        self.log_msg(f"hp at {self.get_hp()}, eating food")
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        if rect := self.find_sprite(self.win.inventory, "cooked-karambwan.png", "items"):
            self.mouse.move_to(rect.random_point())
            self.sleep()
            self.mouse.click()
            self.sleep()
            return True
        return False
    
    def full_trip(self) -> bool:
        return self.get_num_item_in_inv("cooked-karambwan.png", "items") == 0 and self.is_inv_full()

    def atack_monster(self) -> bool:
        for _ in range(5):
            if not self.move_mouse_to_color_obj(self.monster_color):
                self.log_msg("Could not find monster!")
                continue
            if self.get_mouseover_text(contains="Attack") and self.mouse.click(check_red_click=True):
                self.sleep_while_color_moving(self.monster_color, timeout=5)
                return True
        return False

    def return_to_bank(self) -> bool:
        self.log_msg("Returning to bank...")
        # pag.press("f5")
        # self.sleep()
        # for _ in range(5):
        #     if rect := self.find_sprite(self.win.inventory, "ring_of_dueling.png", "items"):
        #         self.mouse.move_to(rect.random_point())
        #         self.sleep()
        #         self.mouse.click()
        #         time.sleep(10)
        #         self.logout_and_stop_script("[END]")
        #         return True        
        pag.press("f4")
        self.sleep()
        self.mouse.move_to(self.win.spellbook_normal[22].random_point())
        self.sleep()
        self.mouse.click()
        time.sleep(10)
        self.logout_and_stop_script("[END]")
        return True
    
    def has_no_hp_bar(self) -> bool:
        for _ in range(20):
            if self.has_hp_bar():
                return False
            self.sleep(0.1)
        return True