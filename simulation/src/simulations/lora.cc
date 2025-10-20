#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/lorawan-module.h"
#include <iostream>
#include <fstream>

using namespace ns3;
using namespace lorawan;

NS_LOG_COMPONENT_DEFINE("SimpleLoraTest");

int main(int argc, char* argv[])
{
    int nDevices = 5;
    double simulationTime = 100;

    CommandLine cmd;
    cmd.AddValue("nDevices", "Number of end devices", nDevices);
    cmd.AddValue("time", "Simulation time (s)", simulationTime);
    cmd.Parse(argc, argv);

    // Enable logging
    LogComponentEnable("SimpleLoraTest", LOG_LEVEL_INFO);

    std::cout << "========================================" << std::endl;
    std::cout << "LoRa Simulation Parameters:" << std::endl;
    std::cout << "  Devices: " << nDevices << std::endl;
    std::cout << "  Time: " << simulationTime << " seconds" << std::endl;
    std::cout << "========================================" << std::endl;

    // Create nodes
    NodeContainer endDevices;
    endDevices.Create(nDevices);
    NodeContainer gateways;
    gateways.Create(1);

    std::cout << "✓ Created " << nDevices << " end devices and 1 gateway" << std::endl;

    // Mobility
    MobilityHelper mobility;
    mobility.SetPositionAllocator("ns3::UniformDiscPositionAllocator",
                                   "rho", DoubleValue(1000),
                                   "X", DoubleValue(0.0),
                                   "Y", DoubleValue(0.0));
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(endDevices);
    mobility.Install(gateways);

    std::cout << "✓ Positioned nodes" << std::endl;

    // Channel
    Ptr<LogDistancePropagationLossModel> loss = CreateObject<LogDistancePropagationLossModel>();
    loss->SetPathLossExponent(3.76);
    loss->SetReference(1, 7.7);

    Ptr<PropagationDelayModel> delay = CreateObject<ConstantSpeedPropagationDelayModel>();
    Ptr<LoraChannel> channel = CreateObject<LoraChannel>(loss, delay);

    std::cout << "✓ Created LoRa channel" << std::endl;

    // Helpers
    LoraPhyHelper phyHelper = LoraPhyHelper();
    phyHelper.SetChannel(channel);

    LorawanMacHelper macHelper = LorawanMacHelper();

    LoraHelper helper = LoraHelper();
    helper.EnablePacketTracking();

    // Install on end devices
    macHelper.SetDeviceType(LorawanMacHelper::ED_A);
    phyHelper.SetDeviceType(LoraPhyHelper::ED);
    helper.Install(phyHelper, macHelper, endDevices);

    std::cout << "✓ Installed LoRa on end devices" << std::endl;

    // Install on gateway
    macHelper.SetDeviceType(LorawanMacHelper::GW);
    phyHelper.SetDeviceType(LoraPhyHelper::GW);
    helper.Install(phyHelper, macHelper, gateways);

    std::cout << "✓ Installed LoRa on gateway" << std::endl;

    // Spreading factors
    macHelper.SetSpreadingFactorsUp(endDevices, gateways, channel);

    std::cout << "✓ Set spreading factors" << std::endl;

    // Application
    PeriodicSenderHelper appHelper = PeriodicSenderHelper();
    appHelper.SetPeriod(Seconds(10));
    appHelper.Install(endDevices);

    std::cout << "✓ Installed applications (sending every 10s)" << std::endl;
    std::cout << "\n▶ Running simulation..." << std::endl;

    Simulator::Stop(Seconds(simulationTime));
    Simulator::Run();

    std::cout << "\n========================================" << std::endl;
    std::cout << "Simulation Results:" << std::endl;
    std::cout << "========================================" << std::endl;

    // Get packet tracker statistics
    LoraPacketTracker& tracker = helper.GetPacketTracker();

    std::cout << "\nPacket Statistics:" << std::endl;
    std::cout << tracker.CountMacPacketsGlobally(Seconds(0), Seconds(simulationTime)) << std::endl;

    // Print per-device results
    for (uint32_t i = 0; i < endDevices.GetN(); i++)
    {
        std::cout << "\nDevice " << i << ":" << std::endl;
        std::cout << "  Position: ";
        Ptr<MobilityModel> mob = endDevices.Get(i)->GetObject<MobilityModel>();
        Vector pos = mob->GetPosition();
        std::cout << "(" << pos.x << ", " << pos.y << ", " << pos.z << ")" << std::endl;

        // Distance to gateway
        Ptr<MobilityModel> gwMob = gateways.Get(0)->GetObject<MobilityModel>();
        Vector gwPos = gwMob->GetPosition();
        double distance = sqrt(pow(pos.x - gwPos.x, 2) + pow(pos.y - gwPos.y, 2));
        std::cout << "  Distance to GW: " << distance << " m" << std::endl;
    }

    std::cout << "\n✓ Simulation complete!" << std::endl;

    Simulator::Destroy();
    return 0;
}
