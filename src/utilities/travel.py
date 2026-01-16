import math
from utilities.geometry import Point, RuneLiteObject
from enum import Enum

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
                 
                 ):
        self.start = start
        self.end = end
        self.step_type = step_type
        self.description = description

class Traveler():
    def __init__(self, travel_steps: list[TravelStep], walker: Walker):
        self.travel_steps = travel_steps
        self.walker = walker

    def travel(self):
        for step in self.travel_steps:
            self.handle_step(step)
            

    def get_start_step(self) -> int:
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
        for _ in range(5):
            if self.walker.travel_to_dest_along_path(step.end, None, self.description):
                break

        if step.step_type is StepType.stairs:
            return False
        elif step.step_type is StepType.door:
            return False
        return False
    
    def format_point()