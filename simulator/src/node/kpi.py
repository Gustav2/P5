from ..config import *

class KPI:
    def __init__(self):
        self.disc_start_time = 0
        self.disc_first_time = 0

        self.disc_e = 0
        self.disc_tries = 0

        self.disc_e_success = 0
        self.disc_success = 0

    def start_discovery(self, listen_time, local_time):
        if self.disc_start_time == 0:
            self.disc_start_time = local_time
        
        self.disc_tries += 1
        self.disc_e += listen_time * E_RECEIVE

    def send_disc_ack(self, listen_time, local_time):
        self.disc_success += 1
        self.disc_e_success = listen_time * E_RECEIVE + E_RX + E_TX
        self.disc_e += E_RX + E_TX

        if self.disc_first_time == 0:
            self.disc_first_time = local_time

    def receive_disc_ack(self, listen_time, local_time):
        self.disc_success += 1
        self.disc_e_success = listen_time * E_RECEIVE + E_RX + E_TX
        self.disc_e += E_RX + E_TX

        if self.disc_first_time == 0:
            self.disc_first_time = local_time

    def get_success_disc_e(self):
        return self.disc_e_success / self.disc_success

    def get_disc_kpis(self, neigbors):
        e_per_cycle = self.disc_e / self.disc_tries

        time_till_success = (self.disc_first_time - self.disc_start_time) / 1_000
        success_rate = len(neigbors) / (NODES - 1) * 100

        return (e_per_cycle, time_till_success, success_rate)