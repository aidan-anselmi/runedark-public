# import math
# import random

# from matplotlib.pyplot import step
# from model.runelite_bot import RuneLiteBot
# from utilities.geometry import Point, RuneLiteObject
# from enum import Enum
# from utilities.color_util import Color
# import time

# from utilities.walker import Walker


# class StepType(Enum):
#     stairs = "stairs"
#     door = "door"
#     house_portal = "house_portal"
#     walk = "walk"

# class TravelStep():
#     def __init__(self, 
#                  start: Point,
#                  end: Point,
#                  step_type: StepType,
#                  description: str = "", 
#                  mouseover_text : str = "",
#                  color : Color = None,
#                  extra_wait_time: float = 0.0
#                  ):
#         self.start = start
#         self.end = end
#         self.step_type = step_type
#         self.description = description
#         self.mouseover_text = mouseover_text
#         self.color = color
#         self.extra_wait_time = extra_wait_time

# class Traveler():
#     def __init__(self, bot: RuneLiteBot, walker: Walker):
#         self.bot = bot
#         self.walker = walker

#     def travel(self, travel_steps: list[TravelStep], retries: int = 5) -> bool:
#         for _ in range(retries):
#             if self.travel_once(travel_steps):
#                 return True
#         return False

#     def travel_once(self, travel_steps: list[TravelStep]) -> bool:
#         step = self.get_start_step(travel_steps)
#         if step == -1:
#             self.bot.log_msg("Could not determine starting travel step.")
#             return False

#         self.bot.log_msg(f"Starting travel at step {step} {travel_steps[step].description}")
#         for step in travel_steps[step:]:
#             self.bot.toggle_run(state="on")
#             if not self.handle_step(step):
#                 self.bot.log_msg(f"Failed to handle travel step: {step.description}")
#                 return False
#             time.sleep(step.extra_wait_time)
#         return True

#     def get_start_step(self, travel_steps: list[TravelStep]) -> int:
#         cur_location = self.get_cur_location()
#         self.bot.log_msg(f"Current location: {cur_location}")
#         if not cur_location:
#             return -1 

#         closest_step = 0
#         closest_dist = float('inf')
#         for i in range(len(travel_steps)):
#             if math.dist(travel_steps[i].start, cur_location) < closest_dist:
#                 closest_dist = math.dist(travel_steps[i].start, cur_location)
#                 closest_step = i
#             if math.dist(travel_steps[i].end, cur_location) < closest_dist:
#                 closest_dist = math.dist(travel_steps[i].end, cur_location)
#                 closest_step = i
#         return closest_step
    
#     def get_cur_location(self) -> Point:
#         cur_location = Point(-1, -1)
#         for _ in range(10):
#             cur_location = self.walker.get_position()
#             if cur_location != Point(-1, -1):
#                 break
#             else:
#                 self.bot.move_camera(horizontal=random.choice([-25, 25]), vertical=0)
#         return cur_location
    
#     def travel_to_step_end(self, step: TravelStep) -> bool:
#         traveled_to = True
#         if step.step_type in [StepType.stairs, StepType.door, StepType.walk]:
#             if math.dist(step.end, self.get_cur_location()) < 6:
#                 return True

#             traveled_to = False
#             for _ in range(5):
#                 if self.walker.travel_to_dest_along_path(step.end, None, self.format_points(step.start, step.end)):
#                     traveled_to = True
#                     break
#         return traveled_to

#     def handle_step(self, step: TravelStep) -> bool:
#         traveled_to = self.travel_to_step_end(step)
#         if not traveled_to:
#             self.bot.log_msg(f"Failed to walk to step end: {step.description}")
#             return False
        
#         if not step.color:
#             step.color = self.bot.cp.hsv.PINK_MARK

#         if step.step_type is StepType.walk:
#             return True
#         if step.step_type is StepType.stairs:
#             return self.click_object_at_step(step)
#         elif step.step_type is StepType.door:
#             if self.bot.find_colors(self.bot.win.game_view, step.color):
#                 return self.click_object_at_step(step)
#             return True
#         return False

#     def format_points(self, p1: Point, p2: Point) -> str:
#         return f"({p1.x}, {p1.y}) -> ({p2.x}, {p2.y})"
    
#     def click_object_at_step(self, step: TravelStep) -> bool:
#         for _ in range(5):
#             if self.bot.move_mouse_to_color_obj(step.color):
#                 if step.mouseover_text and not self.bot.get_mouseover_text(contains=step.mouseover_text):
#                     self.bot.move_camera(horizontal=random.choice([-25, 25]), vertical=0)
#                     continue
#                 if self.bot.mouse.click(check_red_click=True):
#                     time.sleep(.5)
#                     self.bot.sleep_while_color_moving(step.color)
#                     return True
#             else:
#                 self.bot.log_msg(f"Could not find object for step: {step.description}")
#         return False

import math
import random
import time
from abc import ABC, abstractmethod

from model.runelite_bot import RuneLiteBot
from utilities.geometry import Point
from utilities.color_util import Color
from utilities.walker import Walker
import pyautogui as pag

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
        if math.dist(self.end, traveler.get_cur_location()) < 6:
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

    def travel(self, travel_steps: list[TravelStep], retries: int = 5) -> bool:
        for _ in range(retries):
            if self.travel_once(travel_steps):
                return True
        return False
    
    def get_start_step(self, travel_steps: list[TravelStep]) -> int:
        cur_location = self.get_cur_location()
        self.bot.log_msg(f"Current location: {cur_location}")
        if not cur_location:
            return -1 

        closest_step = 0
        closest_dist = 100 # must be within 100 units to start
        for i in range(len(travel_steps)):
            if travel_steps[i].start is None or travel_steps[i].end is None:
                continue
            print(f"start {travel_steps[i].start} cur location: {cur_location}")
            if math.dist(travel_steps[i].start, cur_location) < closest_dist:
                closest_dist = math.dist(travel_steps[i].start, cur_location)
                closest_step = i
            if math.dist(travel_steps[i].end, cur_location) < closest_dist:
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
        if not self.travel_to_end(traveler):
            traveler.bot.log_msg(f"Failed to walk to stairs: {self.description}")
            return False

        return traveler.click_object_at_step(self)

class DoorStep(TravelStep):
    def handle(self, traveler: "Traveler") -> bool:
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
        super().__init__(description, extra_wait_time)
        self.tele_dest = tele_dest

    def handle(self, traveler: "Traveler") -> bool:
        pag.press("f4")
        traveler.bot.sleep()
        if self.tele_dest == "ge":
            traveler.bot.mouse.move_to(traveler.bot.win.spellbook_normal[15].random_point())
        if self.tele_dest == "home":
            traveler.bot.mouse.move_to(traveler.bot.win.spellbook_normal[22].random_point())
        traveler.bot.mouse.click()
        traveler.bot.sleep(lo=4.0, hi=5.0)
        return True