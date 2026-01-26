import math
import random
import time
from abc import ABC, abstractmethod

from model.runelite_bot import RuneLiteBot
from utilities.geometry import Point
from utilities.color_util import Color
from utilities.walker import Walker
import pyautogui as pag
import utilities.ocr as ocr

class TravelStep(ABC):
    def __init__(
        self,
        start: Point = None,
        end: Point = None,
        description: str = "",
        mouseover_text: str = "",
        color: Color = None,
        extra_wait_time: float = 0.0,
    ):
        self.start = start
        self.end = end
        self.description = description
        self.mouseover_text = mouseover_text
        self.color = color
        self.extra_wait_time = extra_wait_time

    @abstractmethod
    def handle(self, traveler: "Traveler") -> bool:
        pass

    def travel_to_end(self, traveler: "Traveler") -> bool:
        if math.dist(self.end, traveler.get_cur_location()) < 4:
            return True

        for _ in range(5):
            if traveler.walker.travel_to_dest_along_path(
                self.end, None, traveler.format_points(self.start, self.end)
            ):
                return True
        return False
    
class Traveler:
    def __init__(self, bot: RuneLiteBot, walker: Walker):
        self.bot = bot
        self.walker = walker

    def travel(self, travel_steps: list[TravelStep], retries: int = 5, after_percent_zoom=None, zoom=True) -> bool:
        if not travel_steps:
            return True

        if zoom:
            self.bot.zoom(out=True)
        for _ in range(retries):
            if self.travel_once(travel_steps):
                if zoom and after_percent_zoom:
                    self.bot.zoom(out=False, percent_zoom=after_percent_zoom)
                return True
        return False
    
    def get_start_step(self, travel_steps: list[TravelStep]) -> int:
        cur_location = self.get_cur_location()
        self.bot.log_msg(f"Current location: {cur_location}")
        if not cur_location:
            return -1 

        closest_step = 0
        closest_dist = 50 # must be within 50 units to start
        for i in range(len(travel_steps)):
            if travel_steps[i].start and math.dist(travel_steps[i].start, cur_location) < closest_dist:
                closest_dist = math.dist(travel_steps[i].start, cur_location)
                closest_step = i
            if travel_steps[i].end and math.dist(travel_steps[i].end, cur_location) < closest_dist:
                closest_dist = math.dist(travel_steps[i].end, cur_location)
                closest_step = i
        return closest_step
    
    def get_cur_location(self) -> Point:
        cur_location = Point(-1, -1)
        for _ in range(10):
            cur_location = self.walker.get_position()
            if cur_location != Point(-1, -1):
                break
            else:
                self.bot.move_camera(horizontal=random.choice([-25, 25]), vertical=0)
        return cur_location
    
    def format_points(self, p1: Point, p2: Point) -> str:
        return f"({p1.x}, {p1.y}) -> ({p2.x}, {p2.y})"
    
    def click_object_at_step(self, step: TravelStep) -> bool:
        for _ in range(5):
            if self.bot.move_mouse_to_color_obj(step.color):
                if step.mouseover_text and not self.bot.get_mouseover_text(contains=step.mouseover_text):
                    self.bot.move_camera(horizontal=random.choice([-25, 25]), vertical=0)
                    continue
                if self.bot.mouse.click(check_red_click=True):
                    time.sleep(.5)
                    self.bot.sleep_while_color_moving(step.color)
                    return True
            else:
                self.bot.log_msg(f"Could not find object for step: {step.description}")
        return False

    def travel_once(self, travel_steps: list[TravelStep]) -> bool:
        start_idx = self.get_start_step(travel_steps)
        if start_idx == -1:
            self.bot.log_msg("Could not determine starting travel step.")
            return False

        self.bot.log_msg(
            f"Starting travel at step {start_idx}: {travel_steps[start_idx].description}"
        )

        for step in travel_steps[start_idx:]:
            self.bot.toggle_run(state="on")

            if not step.color:
                step.color = self.bot.cp.hsv.PINK_MARK

            if not step.handle(self):
                self.bot.log_msg(f"Failed travel step: {step.description}")
                return False

            time.sleep(step.extra_wait_time)

        return True

    
class WalkStep(TravelStep):
    def handle(self, traveler: "Traveler") -> bool:
        return self.travel_to_end(traveler)

class StairsStep(TravelStep):
    def handle(self, traveler: "Traveler") -> bool:
        if self.start and self.end:
            if not self.travel_to_end(traveler):
                traveler.bot.log_msg(f"Failed to walk to stairs: {self.description}")
                return False

        return traveler.click_object_at_step(self)

class DoorStep(TravelStep):
    def handle(self, traveler: "Traveler") -> bool:
        if self.start and self.end:
            if not self.travel_to_end(traveler):
                traveler.bot.log_msg(f"Failed to walk to door: {self.description}")
                return False

        if traveler.bot.find_colors(traveler.bot.win.game_view, self.color):
            return traveler.click_object_at_step(self)

        # Door already open
        return True

class TeleportSpellStep(TravelStep):
    def __init__(
        self,
        tele_dest: str,
        description: str = "",
        extra_wait_time: float = 0.0,
    ):
        super().__init__(description=description, extra_wait_time=extra_wait_time)
        self.tele_dest = tele_dest

    def handle(self, traveler: "Traveler") -> bool:
        pag.press("f4")
        traveler.bot.sleep()
        if self.tele_dest == "ge":
            traveler.bot.mouse.move_to(traveler.bot.win.spellbook_normal[15].random_point())
        if self.tele_dest == "home":
            traveler.bot.mouse.move_to(traveler.bot.win.spellbook_normal[22].random_point())
        if self.tele_dest == "falador":
            traveler.bot.mouse.move_to(traveler.bot.win.spellbook_normal[20].random_point())
        traveler.bot.mouse.click()
        traveler.bot.sleep(lo=4.0, hi=5.0)
        return True
    
class SpiritTreeStep(TravelStep):
    def __init__(
        self,
        tree_key: str,
        color: Color,
        start: Point = None,
        end: Point = None,
        description: str = "",
    ):
        super().__init__(
            start=start,
            end=end,
            description=description,
            color=color,
            mouseover_text="Travel",
        )
        self.tree_key = tree_key

    def handle(self, traveler: "Traveler") -> bool:
        if self.start and self.end:
            if not self.travel_to_end(traveler):
                traveler.bot.log_msg(f"Failed to walk to spirit tree: {self.description}")
                return False

        if not traveler.click_object_at_step(self):
            return False
        
        def in_spirit_tree_menu() -> bool:
            return ocr.find_textbox("Spirit Tree Locations", rect=traveler.bot.win.game_view, font=ocr.QUILL, colors=traveler.bot.cp.bgr.SPIRIT_TREE_MENU_TEXT)

        for _ in range(25):
            if in_spirit_tree_menu():
                break
            time.sleep(.2)
        if not in_spirit_tree_menu():
            traveler.bot.log_msg("Failed to open spirit tree menu.")
            return False

        pag.press(self.tree_key)
        traveler.bot.sleep(lo=4.0, hi=5.0)
        return True
    
class DigsitePendantStep(TravelStep):
    def __init__(
        self,
        rub_key: str,
        description: str = "",
    ):
        super().__init__(
            description=description,
        )
        self.rub_key = rub_key
            
    def handle(self, traveler: "Traveler") -> bool:
        pag.press("f2")
        if pendant := traveler.bot.find_sprite(traveler.bot.win.inventory, "digsite-pendant.png", folder="items"):
            traveler.bot.mouse.move_to(pendant.random_point())
            if traveler.bot.right_click_select_context_menu("Rub") and traveler.bot.wait_till_interface_text("Digsite", font=ocr.QUILL_8, color=traveler.bot.cp.bgr.BLACK):
                traveler.bot.sleep()
                pag.press(self.rub_key)
                traveler.bot.sleep(lo=3.5, hi=5.0)
                return True
                
        return False
    
class HomeGloryStep(TravelStep):
    def __init__(
        self,
        color : Color = None,
        tele_dest: str = "Edgeville",
        start: Point = None,
    ):
        super().__init__(
            description=f"Teleporting to {tele_dest} via Glory",
            start=start,
        )
        self.tele_dest = tele_dest
        self.color = color
            
    def handle(self, traveler: "Traveler") -> bool:
        if self.color is None:
            self.color = traveler.bot.cp.hsv.BLUE_MARK

        if self.tele_dest == "Edgeville":
            if mounted_glory := traveler.bot.find_colors(traveler.bot.win.game_view, self.color):
                mounted_glory = mounted_glory[0]
                traveler.bot.mouse.move_to(mounted_glory.random_point())
                if traveler.bot.get_mouseover_text(contains="Edgeville") and traveler.bot.mouse.click(check_red_click=True):
                    traveler.bot.sleep_while_color_moving(self.color)
                    traveler.bot.sleep(lo=1, hi=2)
                    return True
        # other destinations not soupported yet
        return False
    
class AbyssRingStep(TravelStep):
    def handle(self, traveler: "Traveler") -> bool:
        return False
    
class FairyRingStep(TravelStep):
    def __init__(
        self,
        start: Point = None,
        color: Color = None,
        description: str = "",
    ):
        super().__init__(
            description=description,
            start=start,
            mouseover_text="Last"
        )

        self.color = color

    def handle(self, traveler: "Traveler") -> bool:
        if not self.equip_item(traveler, "dramen-staff.png"):
            traveler.bot.log_msg("Failed to equip Dramen staff for fairy ring.")
            return False

        res = traveler.click_object_at_step(self)
        if res:
            traveler.bot.sleep(lo=3.0, hi=4.0)

        self.loop_equip_item(traveler, "zombie-axe.png")
        return res

    def equip_item(self, traveler: "Traveler", png: str) -> bool:
        if not traveler.bot.is_control_panel_tab_open("inventory"):
            pag.press("f2")
            traveler.bot.sleep()

        rect = traveler.bot.find_sprite(traveler.bot.win.inventory, png, folder="item")
        if not rect:
            return False
        traveler.bot.mouse.move_to(rect.random_point())
        if traveler.bot.get_mouseover_text(contains="Wield"):
            return False
        traveler.bot.mouse.click()
        traveler.bot.sleep()
        return True
    
    def loop_equip_item(self, traveler: "Traveler", png: str) -> bool:
        for _ in range(15):
            if self.equip_item(traveler, png):
                return True
            time.sleep(1)
        return False