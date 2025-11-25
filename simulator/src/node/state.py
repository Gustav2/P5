from enum import Enum

class State(Enum):
    Idle = 0
    Listen = 1
    Receive = 2
    Transmit = 3
