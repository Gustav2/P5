from ..config import *

class KPI:
    def __init__(self):
        self.disc_e_send = 0
        self.disc_sent = 0
        self.disc_e_receive = 0
        self.disc_received = 0

        self.disc_start_time = 0
        self.disc_first_time = 0

        self.sync_sent = 0
        self.acks_received = 0

    def start_discovery(self, local_time):
        if self.disc_start_time == 0:
            self.disc_start_time = local_time

    def send_discovery(self, listen_time):
        self.disc_sent += 1

        listen_e = listen_time * E_RECEIVE
        self.disc_e_send += listen_e + E_TX
        self.disc_e_receive += listen_e

    def receive_discovery(self, local_time):
        self.disc_received += 1
        self.disc_e_receive += E_RX

        if self.disc_first_time == 0:
            self.disc_first_time = local_time

    def get_disc_kpis(self, neigbors):
        e_per_cycle = (self.disc_e_receive + self.disc_e_send) / (self.disc_sent + self.disc_received)

        time_till_success = (self.disc_first_time - self.disc_start_time) / 1_000
        success_rate = len(neigbors) / (NODES - 1) * 100

        return (e_per_cycle, time_till_success, success_rate)