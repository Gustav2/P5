from enum import Enum

class State(Enum):
    Off = 0
    Idle = 1
    Receive = 2
    Transmit = 3
