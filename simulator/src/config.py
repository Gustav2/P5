ONE_DAY = 86_400 # Seconds in one day

RANGE = 800 # Range for all devices in meters
LOW_POWERED_NODES = 18 # Low powered nodes
HIGH_POWERED_NODES = 36 # High powered nodes
NODES = LOW_POWERED_NODES + HIGH_POWERED_NODES # Amount of nodes in the simulation
SIM_TIME = 1 * ONE_DAY # Simulation time in seconds
SUNRISE_TIME, SUNSET_TIME = 8 * 60 * 60, 18 * 60 * 60 # Time of sunrise and sunset in seconds
IS_DAY_CYCLE = False # Is simulation using day cycle or charges infinitely

TX_TIME = 0.0195 # Time used for decoding an incoming tx
TX_LOSS = 0.1 # Chance of loosing a tx
DELAY_RANGE = (0.01, 0.05) # Tx delay range

# All the energy is Joules
E_MAX = 8.82 # Maximum used energy
E_TRESHOLD = 1.62 # Threshold for energy capacity
E_IDLE =  0.00000495 # Energy used in idle mode
E_LISTEN = 0.03564 # Energy used per second to listen to tranmissions
E_TX = 0.0594 # Energy used to transmit the tx
E_RX = E_LISTEN * TX_TIME # Energy used to receive and decode the tx

LISTEN_TIME_RANGE = (5, 10) # Range for time listening
CLOCK_DRIFT_RANGE = (-10, 10) # Range for a clock drift
LISTEN_TIME_RANGE = (10, 30) # Times in seconds to listen to

HIGH_LIGHT_RANGE_LUX = (30, 35) # Number of lux for a high powered device
LOW_LIGHT_RANGE_LUX = (15, 20) # Number of lux for a low powered device
