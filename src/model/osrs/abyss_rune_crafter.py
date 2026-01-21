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


class AbyssRuneCrafter(OSRSBot):
    def __init__(self):
        bot_title = "Exhibit A"
        description = (
            "This example is here to highlight how bots can be further organized by"
            " folders while still being dynamically picked up by the `options_builder`."
        )
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 180
        self.options_set = False
        # self.scrape()

    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Lobster, Small pouch, Medium pouch, Large pouch, Giant pouch, Law rune, Air rune, Earth rune, Pure essence"
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

    def set_directions(self):
        self.mage_point = Point(3105, 3557)
        self.abyss_center = Point(3041,4832)
        self.abyss_radius = 14
        self.law_rift_point = Point(3050,4839)
        self.law_altar_point = Point(2464,4826)

        self.to_abyss_steps = [
            StairsStep(start=Point(3094,3491), end=Point(3089,3517), description="cross wildy ditch", mouseover_text="Cross", color=self.cp.hsv.PINK_MARK),
            StairsStep(start=Point(3089,3523), end=self.mage_point, description="tele to abyss", mouseover_text="Teleport", color=self.cp.hsv.CYAN_MARK, extra_wait_time=2.5),
        ]
        self.to_bank_steps = [
            TeleportSpellStep("home", "tele home"),
            StairsStep(start=Point(1921,5708), description="drink pool", mouseover_text="Drink", color=self.cp.hsv.GREEN_MARK),
            HomeGloryStep(color=self.cp.hsv.BLUE_MARK, start=Point(1967,5698)),
            StairsStep(start=Point(3087,3493), description="bank", mouseover_text="Bank", color=self.cp.hsv.BLUE_MARK),
        ]
        
        # abyss outer ring
        self.abyss_north = Point(3042,4853)
        self.abyss_south = Point(3037, 4810)
        self.abyss_east = Point(3062,4831)
        self.abyss_west = Point(3017,4827)
        self.abyss_north_east = Point(3054,4847)
        self.abyss_south_east = Point(3057,4816)
        self.abyss_south_west = Point(3017,4814)
        self.abyss_north_west = Point(3023,4847)

        # abyss inner ring
        # self.abyss_inner_north = Point(3040,4843)
        # self.abyss_inner_south = Point(3040,4818)
        # self.abyss_inner_east = Point(3052,4832)
        # self.abyss_inner_west = Point(3027,4831)
        # self.abyss_inner_north_east = Point(3048,4842)
        # self.abyss_inner_south_east = Point(3051,4820)
        # self.abyss_inner_south_west = Point(3028,4820)
        # self.abyss_inner_north_west = Point(3027,4846)
        return

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
        self.set_directions()
        self.walker = Walker(self, dest_square_side_length=4)
        self.traveler = Traveler(self, self.walker)

        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        self.start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = self.start_time

        self.repair_pouch = False
        self.runs = 0

        while time.time() - self.start_time < end_time:
            if self.is_inv_full():
                if math.dist(self.traveler.get_cur_location(), self.law_altar_point) < 50:
                    self.craft_runes()
                elif math.dist(self.traveler.get_cur_location(), self.abyss_center) < 50:
                    self.handle_abyss()
                else:
                    self.traveler.travel(self.to_abyss_steps)
            else:
                self.traveler.travel(self.to_bank_steps)
                self.resupply()

            # update progress
            if time.time() - last_update > 300:
                self.update_progress((time.time() - self.start_time) / end_time)
                last_update = time.time()
            # check for no xp gain
            if self.has_not_gained_xp(duration=300):
                self.log_msg("No XP gained for 5 minutes, returning to bank")
                self.logout_and_stop_script()
                return
            self.toggle_run_on_if_enough_energy()
            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.stop()
        return
    
    def enter_abyss_door(self) -> bool:
        door = self.find_colors(self.win.game_view, self.cp.hsv.PINK_MARK)
        if not door:
            self.log_msg("Could not find abyss door.")
            return False
        door = door[0]
        self.mouse.move_to(door.random_point())
        res = self.mouse.click(check_red_click=True)
        if not res:
            return False
        self.sleep_while_color_moving(self.cp.hsv.PINK_MARK, timeout=3)

    def handle_abyss(self) -> bool:
        # on the inside of the ring
        if math.dist(self.traveler.get_cur_location(), self.abyss_center) < self.abyss_radius:
            if self.repair_pouch:
                for _ in range(5):
                    if self.repair_pouches():
                        break
            for _ in range(5):
                if self.enter_law_rift():
                    break
        
        for _ in range(10):
            if not self.find_colors(self.win.game_view, self.cp.hsv.PINK_MARK):
                self.rotate_within_abyss()

        if not self.enter_abyss_door():
            self.log_msg("Could not enter abyss door.")
            return False

        return self.enter_abyss_door()
    
    def rotate_within_abyss(self) -> bool:
        # ordered clockwise around the abyss center
        points = [
            self.abyss_north,
            self.abyss_north_east,
            self.abyss_east,
            self.abyss_south_east,
            self.abyss_south,
            self.abyss_south_west,
            self.abyss_west,
            self.abyss_north_west,
        ]

        cur = self.traveler.get_cur_location()
        # find index of closest point
        dists = [math.dist(cur, p) for p in points]
        min_idx = int(dists.index(min(dists)))

        # choose the next point clockwise
        next_idx = (min_idx + 1) % len(points)
        target_point = points[next_idx]

        # walk to that point using existing walker path formatting
        self.traveler.walker.travel_to_dest_along_path(
            target_point, None, self.traveler.format_points(self.abyss_center, target_point)
        )
        return True

    def repair_pouches(self) -> bool:
        target_point = Point(3039, 4835)
        if math.dist(self.traveler.get_cur_location(), target_point) > 4:
            self.traveler.walker.travel_to_dest_along_path(
                target_point, None, self.traveler.format_points(self.abyss_center, target_point)
            )
            self.sleep_while_color_moving(self.cp.hsv.CYAN_MARK)

        if not self.move_mouse_to_color_obj(self.cp.hsv.CYAN_MARK):
            self.log_msg("Could not find NPC to repair pouches.")
            return False
        if not self.get_mouseover_text(contains="Repairs") or not self.mouse.click(check_red_click=True):
            self.log_msg("could not click NPC to repair pouches.")
            return False

        self.wait_till_interface_text(contains="repair", timeout=5)
        self.repair_pouch = False
        return True
    
    def enter_law_rift(self) -> bool:
        if math.dist(self.traveler.get_cur_location(), self.law_rift_point) > 4:
            self.traveler.walker.travel_to_dest_along_path(
                self.law_rift_point, None, self.traveler.format_points(self.abyss_center, self.law_rift_point)
            )
            self.sleep_while_color_moving(self.cp.hsv.BLUE_MARK)
        if not self.move_mouse_to_color_obj(self.cp.hsv.BLUE_MARK):
            self.log_msg("Could not find law rift.")
            return False
        if not self.get_mouseover_text(contains="Exit") or not self.mouse.click(check_red_click=True):
            self.log_msg("could not click law rift.")
            return False

        self.sleep(lo=2, hi=3)
        return True

    def craft_runes(self) -> bool:
        def click_altar() -> bool:
            altar = self.find_colors(self.win.game_view, self.cp.hsv.PINK_MARK)
            if not altar:
                return False
            altar = altar[0]
            self.mouse.move_to(altar.random_point())
            if not self.get_mouseover_text(contains="Craft"):
                return False
            self.mouse.click()
            self.sleep_while_color_moving(self.cp.hsv.CYAN_MARK)
            return True

        for _ in range(3):
            if click_altar():
                break
        self.click_pouches()
        for _ in range(3):
            if click_altar():
                break
        
        self.runs += 1
        if self.runs > random.randint(25,40):
            self.repair_pouch = True
            self.runs = 0
        return True
    
    def resupply(self) -> bool:
        if not self.is_bank_window_open():
            return False
        if not self.find_sprite(win=self.win.game_view, png="pure-essence-bank.png", folder="items", confidence=0.05):
            self.open_bank_tab(2)

        if rect := self.find_sprite(win=self.win.inventory, png="law-rune.png", folder="items"):
            self.mouse.move_to(rect.random_point())
            self.mouse.click()
            self.sleep()

        def eat_lobster() -> bool:
            if colors := self.find_colors(self.win.inventory, self.cp.hsv.RED_MARK):
                c = colors[0]
                self.mouse.move_to(c.random_point())
                if self.get_mouseover_text(contains="Eat"):
                    self.mouse.click()
                    self.sleep()
                    return True
            return False

        # eat
        i = 0
        while self.get_hp() < 70 and i < 5:
            i += 1
            if eat_lobster():
                continue
            if lobster_rect := self.find_sprite(win=self.win.game_view, png="lobster.png", folder="items"):
                self.mouse.move_to(lobster_rect.random_point())
                self.mouse.click()
                self.sleep(lo=.5, hi=1.5)
            if eat_lobster():
                self.sleep(lo=1, hi=1.5)

        for png in ["earth-rune-bank.png", "air-rune-bank.png"]:
            if not self.find_sprite(win=self.win.inventory, png=png, folder="items"):
                if rect := self.find_sprite(win=self.win.game_view, png=png, folder="items"):
                    self.mouse.move_to(rect.random_point())
                    self.mouse.click()
                    self.sleep()

        if rect := self.find_sprite(win=self.win.game_view, png="pure-essence-bank.png", folder="items", confidence=0.05):
            self.mouse.move_to(rect.random_point())
            self.mouse.click()
            self.sleep()
        else:
            self.logout_and_stop_script("Out of pure essence, stopping script.")
            return False
        self.click_pouches()
        if rect := self.find_sprite(win=self.win.game_view, png="pure-essence-bank.png", folder="items", confidence=0.05):
            self.mouse.move_to(rect.random_point())
            self.mouse.click()
            self.sleep()
        self.sleep()
        pag.press("esc")
        self.sleep()
        return True
    
    def click_pouches(self) -> bool:
        for png in ["small-pouch.png", "medium-pouch.png", "large-pouch.png", "giant-pouch.png"]:
            for _ in range(3):
                if rect := self.find_sprite(win=self.win.inventory, png=png, folder="items"):
                    self.mouse.move_to(rect.random_point())
                    self.mouse.click()
                    self.sleep()
                    break
                else:
                    self.sleep()
        return True