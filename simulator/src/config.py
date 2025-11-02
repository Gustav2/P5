RANGE = 150 # Range for all devices in meters
TX_TIME = 0.05 # Time used for decoding an incoming tx
LISTEN_TIME = 0.1 # Time used to listen to incoming txns
E_THRESHOLD = 1.0 
E_HARVEST_RATE = (0.001, 0.005) # Energy harvesting spectre
E_TX, E_RX = 0.05, 0.02
DELAY_RANGE = (0.01, 0.05)

NODES = 20 # Amount of nodes in the simulation
SIM_TIME = 500_000 # Simulation time in seconds
TX_LOSS = 0.1 # Chance of loosing a tx
