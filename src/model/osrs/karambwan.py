

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

"""
[
{"regionId":11568,"regionX":19,"regionY":47,"z":0,"color":"#FF00FF00"},
{"regionId":11568,"regionX":19,"regionY":44,"z":0,"color":"#FF00FF00"}
]

[{"regionId":9284,"regionX":55,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":20,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":21,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":22,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":43,"regionY":23,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":42,"regionY":24,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":41,"regionY":25,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":41,"regionY":26,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":40,"regionY":27,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":39,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":38,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":37,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":36,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":35,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":34,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":33,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":32,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":31,"regionY":29,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":30,"regionY":30,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":29,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":28,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":27,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":26,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":25,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":25,"regionY":32,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":24,"regionY":33,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":23,"regionY":34,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":23,"regionY":35,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":22,"regionY":36,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":21,"regionY":37,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":20,"regionY":38,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":19,"regionY":39,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":18,"regionY":39,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":18,"regionY":40,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":17,"regionY":41,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":16,"regionY":42,"z":0,"color":"#FF00FF00"}]
[{"regionId":9284,"regionX":55,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":20,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":21,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":44,"regionY":22,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":43,"regionY":23,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":42,"regionY":24,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":41,"regionY":25,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":41,"regionY":26,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":40,"regionY":27,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":39,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":38,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":37,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":36,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":35,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":34,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":33,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":32,"regionY":28,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":31,"regionY":29,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":30,"regionY":30,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":29,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":28,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":27,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":26,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":25,"regionY":31,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":25,"regionY":32,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":24,"regionY":33,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":23,"regionY":34,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":23,"regionY":35,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":22,"regionY":36,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":21,"regionY":37,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":20,"regionY":38,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":19,"regionY":39,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":18,"regionY":39,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":18,"regionY":40,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":17,"regionY":41,"z":0,"color":"#FF00FF00"},{"regionId":9541,"regionX":16,"regionY":42,"z":0,"color":"#FF00FF00"}]
"""

class Karambwan(OSRSBot):
    def __init__(self):
        bot_title = "Karambwan"  # i.e. "<Script Name>"
        description = (
            "<The script description, in some detail, but not so much as to"
            " take up the whole upper half of the page, goes here.>"
        )
        super().__init__(bot_title=bot_title, description=description)
        # We can set default option values here if we'd like, and potentially override
        # needing to open the options panel.
        self.run_time = 120
        self.options_set = False

        self.walker = Walker(self, dest_square_side_length=6)

        self.bank_tile = Point(2384, 4458)
        self.fairy_ring_tile = Point(2412, 4436)

        self.fishing_spot_color = self.cp.hsv.CYAN_MARK
        self.karamja_fairy_ring_color = self.cp.hsv.PURPLE_MARK
        self.zanaris_fairy_ring_color = self.cp.hsv.YELLOW_MARK
        self.bank_deposit_color = self.cp.hsv.GREEN_MARK

        self.scrape()


    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Raw karambwan, Mithril bar"
        # search_string = "Deposit Inventory"
        image_type = ImageType.BANK
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

        self.action_win = self.win.current_action
        self.action_win.top += 59
        # img = self.action_win.screenshot()
        # cv2.imwrite("action_win.png", img)

        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.
        last_update = start_time
        while time.time() - start_time < end_time:
            
            # bank
            if self.is_inv_full():
                if self.find_colors(self.win.game_view, self.karamja_fairy_ring_color):
                    self.click_karamja_fairy_ring()
                elif self.find_colors(self.win.game_view, self.zanaris_fairy_ring_color):
                    self.log_msg("at zanaris fairy ring")
                    self.travel_to(self.bank_tile, None, "zanaris_fairy_ring_to_bank")
                elif self.find_colors(self.win.game_view, self.bank_deposit_color):
                    self.log_msg("at bank deposit")
                    if self.click_color(self.bank_deposit_color, "Deposit"):
                        for _ in range(10):
                            if self.is_bank_deposit_open():
                                break
                            time.sleep(1)
                    self.click_karambwan()
                    self.close_bank()
                elif self.is_bank_deposit_open():
                    self.log_msg("bank deposit open with full inv")
                    self.click_karambwan()
                    self.close_bank()
                else:
                    self.log_msg("Could not find any tags with full inv")

            # return from bank and fish
            else:
                if self.is_bank_deposit_open():
                    self.log_msg("bank deposit open")
                    self.click_karambwan()
                    self.close_bank()
                if self.find_colors(self.win.game_view, self.bank_deposit_color):
                    self.log_msg("at bank deposit")
                    self.travel_to(self.fairy_ring_tile, None, "zanaris_bank_to_fairy_ring")
                elif self.find_colors(self.win.game_view, self.zanaris_fairy_ring_color):
                    self.log_msg("at zanaris fairy ring")
                    self.click_color(self.zanaris_fairy_ring_color, "Last")
                    time.sleep(2)
                elif self.find_colors(self.win.game_view, self.fishing_spot_color):
                    if not self.is_player_doing_action("Fishing", rect=self.action_win) or rd.random_chance(0.05):
                        if self.click_color(self.fishing_spot_color, "Fish"):
                            time.sleep(5)
                else:
                    self.log_msg("Could not find any tags with empty inv")
            
            if time.time() - last_update > 5:
                self.update_progress((time.time() - start_time) / end_time)
                last_update = time.time()

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

    def click_color(self, color: Color, mouseover_text: str) -> bool:
        if rects := self.find_colors(self.win.game_view, color):
            if not rects or len(rects) != 1:
                self.log_msg(f"Could not find color. rects={len(rects)}")
                return False

            rect = rects[0]
            self.mouse.move_to(rect.random_point())
            if self.get_mouseover_text(contains=mouseover_text):
                res = self.mouse.click(check_red_click=True)
                self.sleep_while_color_moving(color)
                return res
        self.log_msg(f"Could not find color.")
        return False
    
    def click_karamja_fairy_ring(self) -> bool:
        self.log_msg("Clicking Karamja fairy ring...")
        if rects := self.find_colors(self.win.game_view, self.karamja_fairy_ring_color):
            if not rects or len(rects) != 1:
                self.log_msg(f"Could not find color. rects={len(rects)}")
                return False

            rect = rects[0]
            self.mouse.move_to(rect.random_point())
            if self.get_mouseover_text(contains="Last"):
                res = self.right_click_select_context_menu("Zanaris")
                self.sleep_while_color_moving(self.karamja_fairy_ring_color)
                return res
        return False
    
    def click_karambwan(self) -> bool:
        """With the bank window open, mouse to the Deposit All button and left-click it.

        Args:
            mouse_speed (str, optional): The speed to move the mouse. Defaults to
                "fast".
        """
        self.log_msg("Clicking karambwan deposit button...")
        sprite = self.find_sprite(
            win=self.win.game_view, png="raw-karambwan.png", folder="items"
        )
        if sprite: 
            self.mouse.move_to(
                sprite.random_point(),
                knotsCount=1,  # Using 0 or 1 here produces more linear movement.
                tween=pytweening.easeOutBack,
                mouseSpeed="fast",
            )
            self.mouse.click()
            self.sleep()
            self.log_msg("Deposited karambwans.")
            self.sleep()
            return True
        return False
    
    def sleep_while_color_moving(self, color: Color, timeout: int = 15) -> None:
        """Sleep while the player is moving towards a color tag.

        Args:
            color (Color): The color tag we are moving towards.
            timeout (int, optional): The maximum time to wait in seconds. Defaults to 15.
        """
        time.sleep(1)
        start_time = time.time()
        while self.find_colors(self.win.game_view, color) and time.time() - start_time < timeout:
            prev = self.find_colors(self.win.game_view, color)
            time.sleep(.2)
            curr = self.find_colors(self.win.game_view, color)
            if prev and curr:
                prev = prev[0].center
                curr = curr[0].center
                if math.dist(prev, curr) < 2:
                    break
            else:
                break
        time.sleep(1)
        return 
    