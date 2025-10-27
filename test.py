import ns.core
import ns.network
import ns.lora
import ns.mobility
import ns.internet
import ns.applications
import ns.lorawan

def main():
    ns.core.LogComponentEnable("LoraChannel", ns.core.LOG_LEVEL_INFO)

    # Create gateway and end device nodes
    gateways = ns.network.NodeContainer()
    gateways.Create(1)

    end_devices = ns.network.NodeContainer()
    end_devices.Create(3)

    # Mobility
    mobility = ns.mobility.MobilityHelper()
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel")
    mobility.Install(gateways)
    mobility.Install(end_devices)

    # Create LoRa channel
    channel = ns.lora.LoraChannelHelper.Default()
    phy_helper = ns.lora.LoraPhyHelper()
    mac_helper = ns.lora.LoraMacHelper()
    helper = ns.lora.LoraHelper()

    phy_helper.SetChannel(channel.Create())

    # Create network
    helper.EnablePacketTracking(True)
    helper.Install(phy_helper, mac_helper, end_devices, gateways)

    # Simulation time
    ns.core.Simulator.Stop(ns.core.Seconds(10))
    ns.core.Simulator.Run()
    ns.core.Simulator.Destroy()

if __name__ == "__main__":
    main()
