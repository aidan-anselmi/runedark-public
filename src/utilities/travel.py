import math
import random
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
        if not color:
            self.color = self.cp.hsv.PINK_MARK

class Traveler():
    def __init__(self, bot: RuneLiteBot, walker: Walker):
        self.bot = bot
        self.walker = walker

    def travel(self, travel_steps: list[TravelStep]):
        self.travel_steps = travel_steps
        step = self.get_start_step(travel_steps)
        self.bot.log_msg(f"Starting travel at step {step} {self.travel_steps[step].description}")
        for step in self.travel_steps[step:]:
            self.handle_step(step)
            

    def get_start_step(self, travel_steps: list[TravelStep]) -> int:
        cur_location = None
        for _ in range(5):
            cur_location = self.walker.get_position()
            if cur_location != Point(-1, -1, -1):
                break
        if not cur_location:
            return -1 

        closest_step = 0
        closest_dist = float('inf')
        for i in range(len(self.travel_steps)):
            if math.dist(self.travel_steps[i].start, cur_location) < closest_dist:
                closest_dist = math.dist(self.travel_steps[i].start, cur_location)
                closest_step = i
        return closest_step

    def handle_step(self, step: TravelStep) -> bool:
        if step.step_type in [StepType.stairs, StepType.door]:
            for _ in range(5):
                if self.walker.travel_to_dest_along_path(step.end, None, self.format_points(step.start, step.end)):
                    break

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