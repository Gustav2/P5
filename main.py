#!/usr/bin/env python3
from ns import ns

# Enable logging
ns.LogComponentEnable("UdpEchoClientApplication", ns.LOG_LEVEL_INFO)
ns.LogComponentEnable("UdpEchoServerApplication", ns.LOG_LEVEL_INFO)

# Create 2 nodes
nodes = ns.NodeContainer()
nodes.Create(2)

# Connect with point-to-point link
p2p = ns.PointToPointHelper()
p2p.SetDeviceAttribute("DataRate", ns.StringValue("5Mbps"))
p2p.SetChannelAttribute("Delay", ns.StringValue("2ms"))
devices = p2p.Install(nodes)

# Add internet stack and assign IPs
ns.InternetStackHelper().Install(nodes)
address = ns.Ipv4AddressHelper()
address.SetBase(ns.Ipv4Address("10.1.1.0"), ns.Ipv4Mask("255.255.255.0"))
interfaces = address.Assign(devices)

# Setup echo server on node 1
server = ns.UdpEchoServerHelper(9)
serverApps = server.Install(nodes.Get(1))
serverApps.Start(ns.Seconds(1.0))
serverApps.Stop(ns.Seconds(10.0))

# Setup echo client on node 0
client = ns.UdpEchoClientHelper(
    ns.InetSocketAddress(interfaces.GetAddress(1), 9).ConvertTo()
)
client.SetAttribute("MaxPackets", ns.UintegerValue(3))
client.SetAttribute("Interval", ns.TimeValue(ns.Seconds(1.0)))
client.SetAttribute("PacketSize", ns.UintegerValue(1024))
clientApps = client.Install(nodes.Get(0))
clientApps.Start(ns.Seconds(2.0))
clientApps.Stop(ns.Seconds(10.0))

# Run simulation
ns.Simulator.Run()
ns.Simulator.Destroy()
print("Simulation complete!")
