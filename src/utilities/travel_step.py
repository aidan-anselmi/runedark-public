from utilities.geometry import Point, RuneLiteObject

class TravelStep():
    def __init__(self, 
                 start: Point,
                 description: str = "", 
                 wait_for_arrival: bool = True
                 ):
        self.destination = destination
        self.description = description
        self.wait_for_arrival = wait_for_arrival
