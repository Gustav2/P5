RANGE = 800 # Range for all devices in meters
NODES = 10 # Amount of nodes in the simulation
SIM_TIME = 6_000 # Simulation time in seconds

TX_TIME = 0.0195 # Time used for decoding an incoming tx
TX_LOSS = 0.1 # Chance of loosing a tx
DELAY_RANGE = (0.01, 0.05) # Tx delay range

# All the energy is Joules
E_MAX = 8.82 # Maximum used energy
E_TRESHOLD = 1.62 # Threshold for energy capacity
E_TX = 0.0594 # Energy used to transmit the tx
E_RX = 0.03564 # Energy used to receive and decode the tx
E_IDLE =  0.00000495 # Energy used to listen to tx

CLOCK_DRIFT_RANGE = (0.001, 0.05) # Range for a clock drift
WAKEUP_POINT_TRESHOLD = 120 # Wake up before meeting for this amount of seconds

LIGHT_RANGE_LUX = (15, 500) # Number of lux for a device