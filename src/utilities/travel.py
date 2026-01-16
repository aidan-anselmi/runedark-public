import math
import random

from matplotlib.pyplot import step
from model.runelite_bot import RuneLiteBot
from utilities.geometry import Point, RuneLiteObject
from enum import Enum
from utilities.color_util import Color
import time

from utilities.walker import Walker


class StepType(Enum):
    stairs = "stairs"
    door = "door"
    house_portal = "house_portal"
    walk = "walk"

class TravelStep():
    def __init__(self, 
                 start: Point,
                 end: Point,
                 step_type: StepType,
                 description: str = "", 
                 mouseover_text : str = "",
                 color : Color = None,
                 ):
        self.start = start
        self.end = end
        self.step_type = step_type
        self.description = description
        self.mouseover_text = mouseover_text
        self.color = color

class Traveler():
    def __init__(self, bot: RuneLiteBot, walker: Walker):
        self.bot = bot
        self.walker = walker

    def travel(self, travel_steps: list[TravelStep], retries: int = 5) -> bool:
        for _ in range(retries):
            if self.travel_once(travel_steps):
                return True
        return False

    def travel_once(self, travel_steps: list[TravelStep]) -> bool:
        step = self.get_start_step(travel_steps)
        if step == -1:
            self.bot.log_msg("Could not determine starting travel step.")
            return False

        self.bot.log_msg(f"Starting travel at step {step} {travel_steps[step].description}")
        for step in travel_steps[step:]:
            self.bot.toggle_run(state="on")
            if not self.handle_step(step):
                self.bot.log_msg(f"Failed to handle travel step: {step.description}")
                return False
        return True

    def get_start_step(self, travel_steps: list[TravelStep]) -> int:
        cur_location = self.get_cur_location()
        self.bot.log_msg(f"Current location: {cur_location}")
        if not cur_location:
            return -1 

        closest_step = 0
        closest_dist = float('inf')
        for i in range(len(travel_steps)):
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
    
    def travel_to_step_end(self, step: TravelStep) -> bool:
        traveled_to = True
        if step.step_type in [StepType.stairs, StepType.door, StepType.walk]:
            if math.dist(step.end, self.get_cur_location()) < 10:
                return True

            traveled_to = False
            for _ in range(5):
                if self.walker.travel_to_dest_along_path(step.end, None, self.format_points(step.start, step.end)):
                    traveled_to = True
                    break
        return traveled_to

    def handle_step(self, step: TravelStep) -> bool:
        traveled_to = self.travel_to_step_end(step)
        if not traveled_to:
            self.bot.log_msg(f"Failed to walk to step end: {step.description}")
            return False
        
        if not step.color:
            step.color = self.bot.cp.hsv.PINK_MARK

        if step.step_type is StepType.walk:
            return True
        if step.step_type is StepType.stairs:
            return self.click_object_at_step(step)
        elif step.step_type is StepType.door:
            if self.bot.find_colors(self.bot.win.game_view, step.color):
                return self.click_object_at_step(step)
            return True
        return False

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
        return False