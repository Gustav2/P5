import numpy as np

def lora_toa(SF, BW, CR, PL, IH=0, Npream=8, CRC=1):
    # CR input must be: 1->4/5, 2->4/6, 3->4/7, 4->4/8
    DE = 1 if (BW == 125000 and SF in [11,12]) else 0

    Rsym = BW / 2**SF

    Tsym = 1 / Rsym
    Tpream = (Npream + 4.25) * Tsym

    numerator = 8*PL - 4*SF + 28 + 16*CRC - 20*IH
    denominator = 4 * (SF - 2*DE)

    Npayload = 8 + max(
        np.ceil(numerator / denominator) * (CR + 4), 0
    )

    Tpayload = Npayload * Tsym
    Tpacket = Tpream + Tpayload
    return Tpacket


def lora_energy_consumption(Tpacket, Trx, Tstandby, Tidle, voltage=3.3, tx_current=29, rx_current=10.8, standby_current=1.6, idle_current=1.5/1000):
    power_tx = voltage * tx_current * Tpacket
    power_rx = voltage * rx_current * Trx
    power_standby = voltage * standby_current * Tstandby
    power_idle = voltage * idle_current * Tidle

    return (power_tx, power_rx, power_standby, power_idle)


# Example
if __name__ == "__main__":
    SF = 7
    BW = 500000
    CR = 3
    PL = 11

    Tpacket = lora_toa(SF, BW, CR, PL)
    Trx = 0.5  # seconds
    Tstandby = 86400  # seconds
    Tidle = 86400  # seconds
    energy_tx, energy_rx, energy_standby, energy_idle = lora_energy_consumption(Tpacket, Trx, Tstandby, Tidle)
    print(f"For Packet Length: {PL} bytes:")
    print(f"TX Energy: {energy_tx:.2f} mJ ({Tpacket:.3f} s)")
    print(f"RX Energy: {energy_rx:.2f} mJ ({Trx:.3f} s)")
    print(f"Standby Energy: {energy_standby:.2f} mJ ({energy_standby/1000:.2f} J) ({Tstandby:.3f} s)")
    print(f"Idle Energy: {energy_idle:.2f} mJ ({energy_idle/1000:.2f} J) ({Tidle:.3f} s)")
    
    #print((0.9083*28-9.2714)*10**-6 * 86400)
    #print((0.9083*50-9.2714)*10**-6 * 86400)
    #print((0.9083*200-9.2714)*10**-6 * 86400)
    #print((0.9083*500-9.2714)*10**-6 * 86400)
    #print((0.9083*6000-9.2714)*10**-6 * 86400)