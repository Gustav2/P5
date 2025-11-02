RANGE = 150 # Range for all devices in meters
NODES = 10 # Amount of nodes in the simulation
SIM_TIME = 100 # Simulation time in seconds

TX_TIME = 0.0195 # Time used for decoding an incoming tx
TX_LOSS = 0.1 # Chance of loosing a tx
DELAY_RANGE = (0.01, 0.05) # Tx delay range

E_TX, E_RX, E_IDLE = 0.000041, 0.0000108, 0.000001 # Consumed energy in A during operations
E_HARVEST_RATE = 0.00015 # Energy harvesting rate for all devices
E_TRESHOLD = 0.00001 # Amount of energy needed to enable idle/listen mode
E_MAX = 0.0001 # Maximum energy for a device