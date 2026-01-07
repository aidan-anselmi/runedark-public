import math
import time
import re

import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.osrs.power_chopper import OSRSPowerChopper
from utilities.geometry import Point, Rectangle
from utilities.mappings import item_ids as iid
from utilities.mappings import locations as loc
from utilities.walker import Walker, WalkPath
from utilities.color_util import Color
from utilities.sprite_scraper import SpriteScraper, ImageType
import pytweening
from pathlib import Path
import cv2
import pyautogui as pag
from dataclasses import dataclass
import utilities.ocr as ocr
import utilities.debug as dbg
import copy
from utilities.color_util import Color, ColorPalette, isolate_colors, isolate_contours

@dataclass
class Contract:
    dest: str
    teak_planks: int
    steel_bars: int
    dest_tile: Point
    completed: bool = False

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

        self.walker = Walker(self, dest_square_side_length=10)

        self.build_color = self.cp.hsv.PINK_MARK
        self.stairs_color = self.cp.hsv.PURPLE_MARK
        self.npc_color = self.cp.hsv.CYAN_MARK
        self.door_color = self.cp.hsv.BLUE_MARK
        self.bank_color = self.cp.hsv.BLUE_MARK
        self.teleport_color = self.cp.hsv.PURPLE_MARK

        self.contract_start_point = Point(2989, 3366)
        self.bank_point = Point(3013, 3356)

    def scrape(self):
        scraper = SpriteScraper()

        # set destination directory to src/images/bot/items (project-relative)
        dest_dir = Path(__file__).resolve().parents[2].joinpath("img", "bot", "items")
        # make sure directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        search_string = "Steel bar, Teak plank"
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

        self.scrape()
        dbg.print_unique_colors(self.win.game_view.screenshot(), top_n=5)
        #game_view = self.win.game_view.screenshot()
        #dbg.save_image("blue.png", isolate_contours(game_view, self.cp.hsv.BLUE))
        dbg.save_image("blue_mark.png", isolate_contours(self.win.game_view.screenshot(), self.cp.hsv.BLUE_MARK))

        self.npc_win = copy.deepcopy(self.win.current_action)
        self.npc_win.left -= 10
        self.npc_win.top += 57

        self.dest_win = copy.deepcopy(self.win.current_action)
        self.dest_win.left -= 10
        self.dest_win.top += 73

        self.plank_win = copy.deepcopy(self.dest_win)
        self.plank_win.top += 34

        self.dest_win.width += 250

        dbg.save_image("plank_win.png", self.plank_win.screenshot())
        dbg.save_image("dest_win.png", self.dest_win.screenshot())
        dbg.save_image("npc_win.png", self.npc_win.screenshot())

        #self.prepare_standard_initial_state()
        self.first_bank = True

        run_time_str = f"{self.run_time // 60}h {self.run_time % 60}m"  # e.g. 6h 0m
        self.log_msg(f"[START] ({run_time_str})", overwrite=True)
        start_time = time.time()
        end_time = int(self.run_time) * 60  # Measured in seconds.

        while time.time() - start_time < end_time:
            contract = self.get_contract()
            if not contract:
                if math.dist(self.walker.get_position(), self.contract_start_point) > 50:
                    self.tele_to("falador")
                else:
                    self.log_msg("Already at dest")
                self.travel_to(self.contract_start_point, None, "falador_to_mahogany_homes_start")
                self.move_mouse_to_color_obj(self.npc_color)
                if not self.mouse.click(check_red_click=True):
                    continue
                self.wait_till_interface_text(texts="Please could", font=ocr.QUILL_8, color=self.cp.hsv.BLACK)
                contract = self.get_contract()
                if not contract:
                    pag.press("space")
                    continue
            if not self.have_required_items(contract):
                self.travel_to(self.bank_point, None, "mahogany_homes_start_to_bank")
                self.sleep_while_color_moving(self.bank_color)
                if not self.move_mouse_to_color_obj(self.bank_color):
                    self.log_msg("Could not find bank")
                    continue
                if not self.get_mouseover_text(contains="Bank"):
                    self.log_msg("Could not find bank mouseover")
                    continue
                if not self.mouse.click(check_red_click=True):
                    self.log_msg("Could not open bank")
                    continue
                if not self.sleep_until_bank_open():
                    self.log_msg("Bank did not open")
                    continue
                self.withdraw_items()
                if not self.have_required_items(contract):
                    self.log_msg("Still do not have required items after withdrawing")
                    continue
            
            if not self.find_colors(self.win.game_view, self.build_color) and not self.find_colors(self.win.game_view, self.stairs_color):
                if math.dist(self.walker.get_position(), contract.dest_tile) > 100:
                     self.tele_to(contract.dest)
                else:
                    self.log_msg("Already at dest")
                self.travel_to(contract.dest_tile, None, f"mahogany_homes_travel_to_{contract.dest}")
                time.sleep(1)
            self.handle_contract()
            self.update_progress((time.time() - start_time) / end_time)
            time.sleep(.1)

        self.update_progress(1)
        self.log_msg("[END]")
        self.stop()

    def have_required_items(self, contract: Contract) -> bool:
        """Check if the player has the required items to start Mahogany Homes.

        Returns:
            bool: True if the player has all required items, False otherwise.
        """
        if not self.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            self.sleep()
        

        if self.get_num_item_in_inv("teak-plank.png", "items") < contract.teak_planks:
            self.log_msg(f"Not enough teak planks. Required: {contract.teak_planks}")
            return False

        if self.get_num_item_in_inv("steel-bar.png", "items") < contract.steel_bars:
            self.log_msg(f"Not enough steel bars. Required: {contract.steel_bars}")
            return False

        return True
    
    def withdraw_items(self) -> bool:
        """Withdraw required items from the bank.

        Returns:
            bool: True if the items were successfully withdrawn, False otherwise.
        """
        if not self.is_bank_window_open():
            self.log_msg("Bank not open")
            return False
        
        if self.first_bank:
            self.open_bank_tab(4)
            self.first_bank = False
        
        bars = self.get_num_item_in_inv("steel-bar.png", "items")
        clicks = 2 - bars
        if clicks > 0:
            rect = self.find_sprite(self.win.game_view, png="steel-bar-bank.png", folder="items")
            self.mouse.move_to(rect.random_point())
            self.sleep()
            for _ in range(clicks):
                self.mouse.click()
                self.sleep()

        rect = self.find_sprite(self.win.game_view, png="teak-plank-bank.png", folder="items")
        self.mouse.move_to(rect.random_point())
        self.sleep()
        self.mouse.click()
        self.sleep()
        
        pag.press("esc")
        self.sleep(lo=1, hi=1.5)
        return True
    
    def task_completed(self):
        return False
    
    def get_contract(self) -> Contract | None:
        res = Contract(dest="", teak_planks=0, steel_bars=1, dest_tile=Point(0, 0))

        if npc_text := ocr.scrape_text(self.npc_win, font=ocr.PLAIN_12, colors=self.cp.rgb.WHITE):
            npc_text = npc_text.strip().lower()
            match npc_text:
                case "jess":
                    res.dest_tile = Point(2621, 3292)
                case "noella":
                    res.dest_tile = Point(2659, 3320)
                case "ross":
                    res.dest_tile = Point(2613, 3316)
                case "larry":
                    #res.dest_tile = Point(3038, 3364)
                    res.dest_tile = Point(3038, 3360)
                case "norman":
                    res.dest_tile = Point(3038, 3344)
                case "tau":
                    res.dest_tile = Point(3047, 3345)
                case "barbara":
                    #res.dest_tile = Point(1750, 3534)
                    res.dest_tile = Point(1746, 3534)
                case "leela":
                    res.dest_tile = Point(1785, 3592)
                case "mariah":
                    #res.dest_tile = Point(1766, 3621)
                    res.dest_tile = Point(1765, 3624)
                case "bob":
                    #res.dest_tile = Point(3238, 3486)
                    res.dest_tile = Point(3243, 3486)
                case "jeff":
                    #res.dest_tile = Point(3239, 3450)
                    res.dest_tile = Point(3244, 3450)
                case "sarah":
                    #res.dest_tile = Point(3235, 3384)
                    res.dest_tile = Point(3235, 3387)

        for text in ["Varrock", "Falador", "Ardougne", "Hosidius"]:
            if ocr.find_textbox(text, rect=self.dest_win, font=ocr.PLAIN_12, colors=self.cp.rgb.WHITE):
                res.dest = text.lower()
                break
        
        if plank_text := ocr.scrape_text(self.plank_win, font=ocr.PLAIN_12, colors=self.cp.rgb.WHITE):
            m = re.search(r"-(\d+)", plank_text)
            if m:
                res.teak_planks = int(m.group(1))
            else:
                nums = re.findall(r"\d+", plank_text)
                if nums:
                    res.teak_planks = int(nums[-1])
        elif plank_text := ocr.find_textbox("All tasks", rect=self.plank_win, font=ocr.PLAIN_12, colors=self.cp.rgb.GREEN_DROPDOWN_TEXT):
            res.completed = True
        else:
            self.log_msg("Could not read plank window")

        self.log_msg(f"Contract: {res}")
        if res.dest == "" or res.dest_tile == Point(0, 0):
            self.log_msg("Could not read contract destination")
            return None
        return res
    
    def tele_to(self, dest: str) -> bool:
        pag.press("f4")
        self.sleep()
        if dest == "falador":
            self.mouse.move_to(self.win.spellbook_normal[20].random_point())
        elif dest == "varrock":
            self.mouse.move_to(self.win.spellbook_normal[15].random_point())
        elif dest == "hosidius":
            self.mouse.move_to(self.win.spellbook_normal[22].random_point())
        elif dest == "ardougne":
            self.mouse.move_to(self.win.spellbook_normal[32].random_point())
        else:
            self.log_msg("dest not recognized")
            return False
        self.sleep()
        self.mouse.click()
        self.sleep_until_color_visible(self.cp.hsv.YELLOW_MARK, timeout=15)

        if dest == "hosidius":
            self.sleep()
            for _ in range(5):
                if not self.move_mouse_to_color_obj(self.teleport_color):
                    continue
                if not self.get_mouseover_text(contains="Enter"):
                    continue
                if not self.mouse.click(check_red_click=True):
                    continue
                break
            self.sleep_until_color_visible(self.cp.hsv.GREEN_MARK, timeout=15)
        return True

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

    def handle_contract(self) -> bool:
        self.log_msg("Handling contract...")
        order = -1        
        self.open_all_doors()
        while self.get_contract().completed == False and (self.find_colors(self.win.game_view, self.stairs_color) or self.find_colors(self.win.game_view, self.build_color)):
            self.build_all_furniture()
            if self.go_up_stairs(order=order):
                self.open_all_doors()

            if order == 0:
                order = -1
            else:
                order = 0

        if not self.find_colors(self.win.game_view, self.npc_color):
            self.go_up_stairs()
        if not self.find_colors(self.win.game_view, self.npc_color):
            self.go_up_stairs(-1)
        self.hand_in()
        return
    
    def open_all_doors(self) -> bool:
        self.log_msg(f"Opening all doors... {self.find_colors(self.win.game_view, self.door_color)}")
        while self.find_colors(self.win.game_view, self.door_color):
            self.open_door()

    def open_door(self) -> bool:
        if self.find_colors(self.win.game_view, self.door_color):
            self.move_mouse_to_color_obj(self.door_color)
            res = self.mouse.click(check_red_click=True)
            self.sleep_while_color_moving(self.door_color)
            if not res:
                return self.open_door()
        return False

    def go_up_stairs(self, order = 0) -> bool:
        if self.find_colors(self.win.game_view, self.stairs_color):
            while not self.get_mouseover_text(contains="Climb"):
                self.move_mouse_to_color_obj(self.stairs_color, order=order)
                self.sleep()
            if self.mouse.click(check_red_click=True):
                self.sleep_while_color_moving(self.stairs_color)
                return True
        return False

    def hand_in(self) -> bool:
        self.log_msg("Handing in")
        if not self.find_colors(self.win.game_view, self.npc_color):
            self.log_msg("Could not find hand in option")
            return False
        self.move_mouse_to_color_obj(self.npc_color)
        if not self.get_mouseover_text(contains="Talk"):
            self.log_msg("Mouseover text did not match for hand in")
            return False
        if not self.mouse.click(check_red_click=True):
            self.log_msg("Could not click to hand in")
            return False

        if not self.wait_till_interface_text(texts="Ive finished", font=ocr.QUILL_8, color=self.cp.hsv.BLACK):
            return False
        pag.press("space")
        if not self.wait_till_interface_text(texts="Thank you", font=ocr.QUILL_8, color=self.cp.hsv.BLACK):
            return False
        pag.press("space")
        if not self.wait_till_interface_text(texts="Yes", font=ocr.QUILL_8, color=self.cp.hsv.BLACK):
            return False
        if rd.random_chance(0.8):
            pag.press("space")
        
        return True
    
    def build_all_furniture(self) -> bool:
        while self.find_colors(self.win.game_view, self.build_color):
            self.move_mouse_to_color_obj(self.build_color)
            self.mouse.click(check_red_click=True)
            self.sleep_while_color_moving(self.build_color)
            if self.get_cant_reach():
                if not self.go_up_stairs():
                    self.open_all_doors()
        
        return True