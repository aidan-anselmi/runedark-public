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
import cv2
import random as rd
import pyautogui as pag
from dataclasses import dataclass
import utilities.ocr as ocr

@dataclass
class Contract:
    dest: str
    teak_planks: int
    steel_bars: int

class MahoganyHomes(OSRSBot):
    def __init__(self):
        bot_title = "Mahogany Homes"  # i.e. "<Script Name>"
        description = (
            "This script automates the Mahogany Homes quest in Old School RuneScape."
            " It handles all aspects of the quest, including starting the quest, "
            "collecting items, and completing objectives."
        )
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 120
        self.options_set = False

        self.walker = Walker(self, dest_square_side_length=6)

        self.build_color = self.cp.hsv.GREEN_MARK
        self.stairs_color = self.cp.hsv.PURPLE_MARK
        self.npc_color = self.cp.hsv.CYAN_MARK
        self.door_color = self.cp.hsv.BLUE_MARK

        self.contract_start_point = Point(2989, 3366)
        self.bank_point = Point(3013, 3356)

    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Steel bar, Teak Plank"
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

        self.dest_win = self.win.current_action
        self.dest_win.top += 73
        #img = self.dest_win.screenshot()
        #cv2.imwrite("dest_win.png", img)


        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = start_time

        while time.time() - start_time < end_time:
            contract = self.get_contract()
            continue 
            if not contract:
                self.tele_to("falador")
                self.travel_to(self.contract_start_point, None, "mahogany_homes_start")
                self.find_and_mouse_to_marked_object(self.npc_color, "Last")
                self.mouse.click()
                
            
            if time.time() - last_update > 300:
                self.update_progress((time.time() - start_time) / end_time)
                last_update = time.time()

            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.stop()

    def have_required_items(self):
        """Check if the player has the required items to start Mahogany Homes.

        Returns:
            bool: True if the player has all required items, False otherwise.
        """
        planks, bars = self.get_required_items()

        if self.get_num_item_in_inv("teak-plank.png", "items") < planks:
            self.log_msg(f"Not enough teak planks. Required: {planks}")
            return False

        if self.get_num_item_in_inv("steel-bar.png", "items") < bars:
            self.log_msg(f"Not enough steel bars. Required: {bars}")
            return False

        return True

    def get_required_items(self):
        return 0, 0
    
    def task_completed(self):
        return False
    
    def get_contract(self) -> Contract | None:
        res = Contract(dest="", teak_planks=0, steel_bars=0)
        text = ocr.scrape_text(self.dest_win, font=ocr.PLAIN_11, colors=self.cp.hsv.OFF_WHITE_TEXT)
        self.log_msg(f"dest text: {text}")

        for text in ["Varrock", "Falador", "Ardougne"]:
            if ocr.find_textbox(text, rect=self.dest_win, font=ocr.PLAIN_11, colors=self.cp.hsv.WHITE):
                res.dest = text
                break

        if res.dest == "":
            self.log_msg("Could not read contract destination")
            return None

        self.log_msg(f"Contract: {res}")
        return res
    
    def hand_in(self) -> bool:
        if not self.find_colors(self.win.game_view, self.npc_color):
            self.log_msg("Could not find hand in option")
            return False
        if not self.get_mouseover_text(contains="Talk"):
            self.log_msg("Mouseover text did not match for hand in")
            return False
        if not self.mouse.click(check_red_click=True):
            return False

        self.wait_till_interface_text(texts="I've finished")
        pag.press("space")
        self.wait_till_interface_text(texts="Thank you")
        pag.press("space")
        self.wait_till_interface_text(texts="Yes")
        if rd.random_chance(0.8):
            pag.press("space")
        
        return True
    
    def tele_to(self, dest: str) -> bool:
        pag.press("f4")
        self.sleep()
        if dest == "falador":
            self.mouse.move_to(self.win.spellbook_normal[20].random_point())
        elif dest == "varrock":
            self.mouse.move_to(self.win.spellbook_normal[15].random_point())
        else:
            return False
        

        return self.mouse.click(check_red_click=True)
    
    
    def build_furniture(self) -> bool:
        if not self.move_mouse_to_color_obj(self.build_color, self.action_win):
            self.log_msg("Could not find build furniture")
            return False
        
        if not self.get_mouseover_text(contains=["Build", "Repair", "Remove"]):
            self.log_msg("Mouseover text did not match for building furniture")
            return False
        
        return self.mouse.click(check_red_click=True)
    
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