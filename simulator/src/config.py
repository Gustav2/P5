RANGE = 800 # Range for all devices in meters
NODES = 50 # Amount of nodes in the simulation
SIM_TIME = 2* 86_400 # Simulation time in seconds
START_SYNC_AFTER = 86_400 # Time in simulation after sync starts
SUNRISE_TIME, SUNSET_TIME = 8 * 24 * 60, 16 * 24 * 60 # Time of sunrise and sunset in seconds

TX_TIME = 0.0195 # Time used for decoding an incoming tx
TX_LOSS = 0.1 # Chance of loosing a tx
DELAY_RANGE = (0.01, 0.05) # Tx delay range

# All the energy is Joules
E_MAX = 8.82 # Maximum used energy
E_TRESHOLD = 1.62 # Threshold for energy capacity
E_TX = 0.0594 # Energy used to transmit the tx
E_RX = 0.03564 # Energy used to receive and decode the tx
E_IDLE =  0.00000495 # Energy used to listen to tx

CLOCK_DRIFT_RANGE = (-3, 3) # Range for a clock drift
WAKEUP_POINT_TRESHOLD = 60 # Wake up before meeting for half of this amount of seconds and go to sleep after another half
MEETUP_INTERVAL = 150 # Amount of seconds to have meeting point at
WAKEUP_RANGE = (100, 150) # Range for random wake up if device has no discoveries yet

LIGHT_RANGE_LUX = (15, 100) # Number of lux for a device