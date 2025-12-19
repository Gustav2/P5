LOW_POWERED_NODES = 18          # Low powered nodes
HIGH_POWERED_NODES = 36         # High powered nodes
NODES = LOW_POWERED_NODES + HIGH_POWERED_NODES # Amount of nodes in the simulation

CLOCK_DRIFT_ENABLED = True     # Enable clock drift simulation
CLOCK_DRIFT_PER_DAY = 500_000   # Max clock drift per day

RUNS = 1                       # Number of runs for the simulation
SIM_DAYS = 100                  # Actual number of days to simulate
SEED = 42                       # Seed for random generator
    
ONE_DAY = 86_400_000            # One day in miliseconds
SIM_TIME = SIM_DAYS * ONE_DAY   # Simulation time in miliseconds
PT_TIME = 14.89                 # Time in miliseconds used for decoding an incoming packet
PT_LOSS = 0.005                 # Chance of loosing a packet
DELAY_RANGE = (10, 50)          # Packet delay range in miliseconds

# All the energy is Joules or Joules/miliseconds
E_MAX = 8.82                        # Maximum used energy
E_TRESHOLD = 1.62                   # Threshold for energy capacity
E_IDLE =  0.00000495 / 1_000        # Energy used in idle mode per millisecond
E_RECEIVE = 0.03564 / 1_000         # Energy used per millisecond in receiveing mode
E_TX = 0.1023 / 1_000 * PT_TIME     # Energy used to transmit the packet
E_RX = E_RECEIVE * PT_TIME          # Energy used to receive and decode the packet

LISTEN_TIME_RANGE = (1000, 2000)    # Range for time listening in milliseconds

SYNC_INTERVAL = 7 * ONE_DAY         # How ofter nodes perform sync
SYNC_TIME = 200                     # For how long sync is operated
SYNC_TIME_RANGE = (75, 125)        # For how long node listens for a sync message, before sending one
SYNC_PREPARATION_TIME = 45 * 60 * 1_000 # For how long before a sync node starts chraging

HIGH_LIGHT_RANGE_LUX = (100, 1000)  # Number of lux for a high powered device
LOW_LIGHT_RANGE_LUX = (16, 100)     # Number of lux for a low powered device

NODE_START_TIMES = (0, 3*ONE_DAY)  # Possible start times for nodes in milliseconds