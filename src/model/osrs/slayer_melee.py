import math
import time
from typing import List

import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.osrs.power_chopper import OSRSPowerChopper
from utilities.geometry import Point, RuneLiteObject
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

        self.walker = Walker(self, dest_square_side_length=4)

        self.monster_color = self.cp.hsv.CYAN_MARK
        self.bank_color = self.cp.hsv.BLUE_MARK
        self.food_color = Color(((0, 245, 245), (1, 255, 255)))

        self.scrape()

        
        self.task = ""

        # elf task
        # self.task = "Elves"
        # self.task_tile = Point(2331,3173)
        # self.bank_tile = Point(2352,3163)

        # Suqah task
        # self.task = "Suqah"
        # self.task_tile = Point(2331,3173)
        # self.bank_tile = Point(2137,3854)


    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Cooked karambwan, Ring of dueling, Herb sack, Gem bag"
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
        self.start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = self.start_time
        xp_timestamp = time.time()

        self.toggle_auto_retaliate(state="on")
        self.sleep()
        pag.press("f2")  # open combat tab

        self.has_no_hp_bar_consec = 0
        self.last_attack_monster_timestamp = 0
        self.last_out_of_combat_timestamp = 0


        while time.time() - self.start_time < end_time:
            if self.has_not_gained_xp(duration=300):
                self.log_msg("No XP gained for 5 minutes, returning to bank")
                self.return_to_bank()
                return

            # heal
            if self.get_hp() != -1:
                while self.get_hp() <= 60 and self.eat_food():
                    self.sleep()
                if self.get_hp() <= 40:
                    self.log_msg("HP low after eating, returning to banks")
                    self.return_to_bank()

            # loot
            if self.find_ground_items() and self.is_inv_full():
                self.eat_food()
            self.high_alch_item()
            self.pickup_ground_item()                

            # fight 
            if self.out_of_combat() or self.has_no_hp_bar():
                self.atack_monster()

            # bank
            if self.full_trip() or self.check_task_completed():
                self.return_to_bank()            

            # update progress
            if time.time() - last_update > 300:
                self.update_progress((time.time() - self.start_time) / end_time)
                last_update = time.time()

            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.logout_and_stop_script("[END]")

    def out_of_combat(self) -> bool:
        if time.time() - self.last_out_of_combat_timestamp < 5:
            return False
        res = self.check_idle_notifier_status("out_of_combat")
        if res:
            self.last_out_of_combat_timestamp = time.time()
        return res

    def eat_food(self) -> bool:
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        if rect := self.get_food_rects():
            rect = rect[-1]
            self.mouse.move_to(rect.random_point())
            self.sleep()
            self.mouse.click()
            self.sleep()
            return True
        return False
    
    def get_food_rects(self) -> List[RuneLiteObject]:
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        return self.find_colors(self.win.inventory, self.food_color)

    def full_trip(self) -> bool:
        if self.is_inv_full():
            self.fill_herb_sack()
        if self.is_inv_full():
            self.fill_gem_bag()         
        res = len(self.get_food_rects()) == 0 and len(self.get_food_rects()) == 0 and self.is_inv_full()
        if res:
            self.log_msg("Inventory full, returning to bank")
        return res

    def atack_monster(self) -> bool:
        if self.last_attack_monster_timestamp + 3 > time.time():
            return False
        
        for i in range(10):
            if not self.move_mouse_to_color_obj(self.monster_color):
                if i == 9:
                    self.log_msg("Could not find monster to attack")
                    if self.task:
                        self.travel_to(self.task_tile, None, f"bank_to_{self.task.lower()}_task")
                continue
            if self.get_mouseover_text(contains="Attack") and self.mouse.click(check_red_click=True):
                self.last_attack_monster_timestamp = time.time()
                return True
        return False

    def return_to_bank(self) -> bool:
        self.log_msg("Returning to bank...")
        if self.task == "Elves" or self.task == "Suqah":
            return self.run_and_back()

        return self.bank_castle_wars()
    
    def bank_castle_wars(self) -> bool:
        pag.press("f4")
        self.sleep()
        self.mouse.move_to(self.win.spellbook_normal[22].random_point())
        self.sleep()
        self.mouse.click()
        time.sleep(10)
        self.stop()
        return True
    
    def run_and_back(self) -> bool:
        self.travel_to(self.bank_tile, None, f"{self.task}_task_to_bank")
        self.resupply()
        if len(self.get_food_rects()) > 0:
            self.travel_to(self.task_tile, None, f"bank_to_{self.task.lower()}_task")
            return True
        return False
    
    def resupply(self) -> bool:
        for i in range(5):
            self.move_mouse_to_color_obj(self.bank_color)
            if self.get_mouseover_text(contains="Bank") and self.mouse.click(check_red_click=True):
                break
            if i == 4:
                self.log_msg("Could not find bank to resupply")
                return False
        self.sleep_until_bank_open()

        for i in range(6, 28):
            if self.is_inv_slot_full(i):
                self.mouse.move_to(self.win.inventory_slots[i].random_point())
                self.mouse.click()
                self.sleep(lo=.3, hi=.5)

        self.open_bank_tab(3)
        if bwans := self.find_sprite(self.win.game_view, "cooked-karambwan-bank.png", "items"):
            self.mouse.move_to(bwans.random_point())
            self.sleep()
            self.mouse.click()
            self.sleep()
        pag.press("esc")
        return True

    def has_no_hp_bar(self) -> bool:
        if self.has_hp_bar():
            return False

        if self.has_no_hp_bar_consec % 50 == 0:
            self.has_no_hp_bar_consec = 1
            return True
        else:
            self.has_no_hp_bar_consec += 1
        return False
    
    def fill_herb_sack(self) -> bool:
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        if rect := self.find_sprite(self.win.inventory, "herb-sack.png", "items"):
            self.mouse.move_to(rect.random_point())
            self.sleep()
            self.mouse.click()
            self.sleep()
            return True
        return False
    
    def fill_gem_bag(self) -> bool:
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        if rect := self.find_sprite(self.win.inventory, "gem-bag.png", "items"):
            self.mouse.move_to(rect.random_point())
            self.sleep()
            self.mouse.click()
            self.sleep()
            return True
        return False

    def check_task_completed(self) -> bool:
        if self.get_chatbox_text(contains="Slayer", colors=self.cp.bgr.OFF_RED_TEXT):
            # can't finish task for first 3 minutes of running 
            if self.start_time + 180 > time.time():
                return False

            self.log_msg("Slayer task completed!")
            return True
        return False

    def travel_to(self, tile_coord: Point, walk_path: WalkPath, dest_name: str, dist_threshold: int = 5) -> None:
        if math.dist(self.walker.get_position(), tile_coord) <= dist_threshold:
            self.log_msg(f"Already at {dest_name}.")
            return
        
        self.log_msg(f"Traveling to {dest_name}...")
        if walk_path and self.walker.travel_to_dest_along_path(
            tile_coord,
            walk_path,
            dest_name,
        ):
            self.log_msg(f"Arrived: {dest_name}")
        else:
            self.log_msg(f"Failed to arrive at {dest_name}.")
        while self.is_traveling():
            self.sleep()