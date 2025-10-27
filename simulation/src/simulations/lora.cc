#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/lorawan-module.h"
#include "ns3/propagation-module.h"
#include "ns3/energy-module.h"
#include <fstream>
#include <map>

using namespace ns3;
using namespace lorawan;
using namespace energy;

NS_LOG_COMPONENT_DEFINE("LoraEnergyDiscovery");

// Energy harvesting scenarios
enum EnergyHarvestScenario
{
    NO_HARVESTING = 0,      // No energy harvesting
    CONSTANT_SOLAR = 1,     // Regular artificial lighting (100-2000 lx)
    DAY_NIGHT_CYCLE = 2,    // Day/night cycle with varying light
    LOW_LIGHT = 3,          // Dark spots/shadows (10-100 lx)
    HYBRID = 4              // Combination of scenarios
};

// Discovery protocol types
enum DiscoveryProtocol
{
    BEACON_BASED = 0,       // Periodic beacon transmission
    ALOHA_DISCOVERY = 1,    // Random access with backoff
    SCHEDULED_LISTENING = 2, // Duty-cycled listening
    ADAPTIVE_DISCOVERY = 3   // Energy-aware adaptive discovery
};

// Global statistics
struct NodeStats
{
    uint32_t nodeId;
    double initialEnergy;
    double finalEnergy;
    double energyConsumed;
    double energyHarvested;
    uint32_t beaconsSent;
    uint32_t beaconsReceived;
    bool discovered;
};

std::map<uint32_t, NodeStats> nodeStatistics;

// Energy harvesting tracker
// Tracks energy harvested from solar cells over time
class EnergyHarvestingTracker : public Object
{
public:
    static TypeId GetTypeId(void);
    EnergyHarvestingTracker();
    virtual ~EnergyHarvestingTracker();

    void SetEnergySource(Ptr<EnergySource> source);
    void SetScenario(EnergyHarvestScenario scenario);
    void SetBaseRate(double rate);
    void Start();
    void Stop();
    double GetTotalHarvested() const { return m_totalHarvested; }

private:
    void Update();
    double CalculateHarvestingRate();

    Ptr<EnergySource> m_source;
    EnergyHarvestScenario m_scenario;
    double m_baseRate;
    double m_totalHarvested;
    Time m_updateInterval;
    EventId m_updateEvent;
    Time m_startTime;
};

TypeId
EnergyHarvestingTracker::GetTypeId(void)
{
    static TypeId tid = TypeId("EnergyHarvestingTracker")
        .SetParent<Object>()
        .SetGroupName("Energy");
    return tid;
}

EnergyHarvestingTracker::EnergyHarvestingTracker()
    : m_scenario(NO_HARVESTING),
      m_baseRate(0.00125),
      m_totalHarvested(0.0),
      m_updateInterval(Seconds(1.0))
{
}

EnergyHarvestingTracker::~EnergyHarvestingTracker()
{
    if (m_updateEvent.IsPending())
    {
        Simulator::Cancel(m_updateEvent);
    }
}

void
EnergyHarvestingTracker::SetEnergySource(Ptr<EnergySource> source)
{
    m_source = source;
}

void
EnergyHarvestingTracker::SetScenario(EnergyHarvestScenario scenario)
{
    m_scenario = scenario;
}

void
EnergyHarvestingTracker::SetBaseRate(double rate)
{
    m_baseRate = rate;
}

void
EnergyHarvestingTracker::Start()
{
    m_startTime = Simulator::Now();
    Update();
}

void
EnergyHarvestingTracker::Stop()
{
    if (m_updateEvent.IsPending())
    {
        Simulator::Cancel(m_updateEvent);
    }
}

double
EnergyHarvestingTracker::CalculateHarvestingRate()
{
    if (m_scenario == NO_HARVESTING)
    {
        return 0.0;
    }

    double elapsed = (Simulator::Now() - m_startTime).GetSeconds();
    double rate = 0.0;

    switch (m_scenario)
    {
        case CONSTANT_SOLAR:
            // Regular artificial lighting (100-2000 lx)
            // Epishine LEH3_50x50_6: 50µW/cm² * 25cm² = 1.25mW
            rate = m_baseRate; // 0.00125 W default
            break;

        case DAY_NIGHT_CYCLE:
            {
                // 12h day/night cycle
                // Day: regular lighting, Night: low light
                double timeOfDay = fmod(elapsed, 43200); // 12h cycles
                if (timeOfDay < 21600) // Day (0-6h)
                {
                    // Sine wave for realistic variation during day
                    rate = m_baseRate * sin((timeOfDay / 21600) * M_PI);
                }
                else // Night (6-12h)
                {
                    // Low light: 5% of regular (10-100 lx range)
                    rate = m_baseRate * 0.05;
                }
            }
            break;

        case LOW_LIGHT:
            // Dark spots / shadow scenario (10-100 lx)
            // About 5% of regular lighting
            rate = m_baseRate * 0.05; // ~62.5 µW for default 1.25mW base
            break;

        case HYBRID:
            {
                // Combination: solar + minimal ambient RF
                double timeOfDay = fmod(elapsed, 43200);
                double solar = 0.0;
                if (timeOfDay < 21600)
                {
                    solar = m_baseRate * sin((timeOfDay / 21600) * M_PI);
                }
                else
                {
                    solar = m_baseRate * 0.05;
                }
                // Small contribution from ambient RF (negligible)
                double rf = m_baseRate * 0.001;
                rate = solar + rf;
            }
            break;

        default:
            rate = 0.0;
    }

    return rate;
}

void
EnergyHarvestingTracker::Update()
{
    double rate = CalculateHarvestingRate();
    double harvestedEnergy = rate * m_updateInterval.GetSeconds();
    m_totalHarvested += harvestedEnergy;

    // Note: We track harvesting but don't add it back to the source
    // This is for statistics only - real implementation would need
    // proper energy source integration

    m_updateEvent = Simulator::Schedule(m_updateInterval,
                                        &EnergyHarvestingTracker::Update,
                                        this);
}

// Discovery beacon application
// Simulates different discovery protocols for LoRa devices
class DiscoveryBeaconApp : public Application
{
public:
    static TypeId GetTypeId(void);
    DiscoveryBeaconApp();
    virtual ~DiscoveryBeaconApp();

    void SetProtocol(DiscoveryProtocol protocol);
    void SetBeaconInterval(Time interval);
    void SetListenInterval(Time interval);
    uint32_t GetBeaconsSent() const { return m_beaconsSent; }
    uint32_t GetBeaconsReceived() const { return m_beaconsReceived; }

private:
    virtual void StartApplication(void);
    virtual void StopApplication(void);

    void SendBeacon(void);
    void StartListening(void);
    void StopListening(void);

    DiscoveryProtocol m_protocol;
    Time m_beaconInterval;
    Time m_listenInterval;
    EventId m_beaconEvent;
    EventId m_listenEvent;
    bool m_listening;
    uint32_t m_beaconsSent;
    uint32_t m_beaconsReceived;
    Ptr<UniformRandomVariable> m_random;
};

TypeId
DiscoveryBeaconApp::GetTypeId(void)
{
    static TypeId tid = TypeId("DiscoveryBeaconApp")
        .SetParent<Application>()
        .SetGroupName("Applications")
        .AddConstructor<DiscoveryBeaconApp>();
    return tid;
}

DiscoveryBeaconApp::DiscoveryBeaconApp()
    : m_protocol(BEACON_BASED),
      m_beaconInterval(Seconds(60.0)),
      m_listenInterval(Seconds(30.0)),
      m_listening(false),
      m_beaconsSent(0),
      m_beaconsReceived(0)
{
    m_random = CreateObject<UniformRandomVariable>();
}

DiscoveryBeaconApp::~DiscoveryBeaconApp()
{
}

void
DiscoveryBeaconApp::SetProtocol(DiscoveryProtocol protocol)
{
    m_protocol = protocol;
}

void
DiscoveryBeaconApp::SetBeaconInterval(Time interval)
{
    m_beaconInterval = interval;
}

void
DiscoveryBeaconApp::SetListenInterval(Time interval)
{
    m_listenInterval = interval;
}

void
DiscoveryBeaconApp::StartApplication(void)
{
    NS_LOG_INFO("Starting discovery on node " << GetNode()->GetId());

    switch (m_protocol)
    {
        case BEACON_BASED:
            // Regular periodic beacons with constant listening
            m_beaconEvent = Simulator::Schedule(m_beaconInterval,
                                               &DiscoveryBeaconApp::SendBeacon,
                                               this);
            StartListening();
            break;

        case ALOHA_DISCOVERY:
            {
                // Random access - random initial delay
                double randomDelay = m_random->GetValue(0, m_beaconInterval.GetSeconds());
                m_beaconEvent = Simulator::Schedule(Seconds(randomDelay),
                                                   &DiscoveryBeaconApp::SendBeacon,
                                                   this);
                StartListening();
            }
            break;

        case SCHEDULED_LISTENING:
            // Duty-cycled listening to save energy
            StartListening();
            m_listenEvent = Simulator::Schedule(m_listenInterval,
                                               &DiscoveryBeaconApp::StopListening,
                                               this);
            m_beaconEvent = Simulator::Schedule(m_beaconInterval,
                                               &DiscoveryBeaconApp::SendBeacon,
                                               this);
            break;

        case ADAPTIVE_DISCOVERY:
            // Energy-aware - could adjust based on remaining energy
            StartListening();
            m_beaconEvent = Simulator::Schedule(m_beaconInterval,
                                               &DiscoveryBeaconApp::SendBeacon,
                                               this);
            break;
    }
}

void
DiscoveryBeaconApp::StopApplication(void)
{
    if (m_beaconEvent.IsPending())
    {
        Simulator::Cancel(m_beaconEvent);
    }
    if (m_listenEvent.IsPending())
    {
        Simulator::Cancel(m_listenEvent);
    }
}

void
DiscoveryBeaconApp::SendBeacon(void)
{
    m_beaconsSent++;

    // Simplified: listening nodes receive beacons
    // In reality, this would go through the network stack
    if (m_listening)
    {
        m_beaconsReceived++;
    }

    // Schedule next beacon based on protocol
    if (m_protocol == ALOHA_DISCOVERY)
    {
        // ALOHA: random backoff
        double randomDelay = m_random->GetValue(0, m_beaconInterval.GetSeconds());
        m_beaconEvent = Simulator::Schedule(Seconds(randomDelay),
                                           &DiscoveryBeaconApp::SendBeacon,
                                           this);
    }
    else
    {
        // Fixed interval
        m_beaconEvent = Simulator::Schedule(m_beaconInterval,
                                           &DiscoveryBeaconApp::SendBeacon,
                                           this);
    }
}

void
DiscoveryBeaconApp::StartListening(void)
{
    m_listening = true;
}

void
DiscoveryBeaconApp::StopListening(void)
{
    m_listening = false;

    if (m_protocol == SCHEDULED_LISTENING)
    {
        // Schedule next listening period
        m_listenEvent = Simulator::Schedule(m_beaconInterval,
                                           &DiscoveryBeaconApp::StartListening,
                                           this);
    }
}

// Main simulation
int main(int argc, char *argv[])
{
    // Realistic simulation parameters based on:
    // - Epishine LEH3_50x50_6 solar cells (25 cm², 50µW/cm²)
    // - Semtech SX127X LoRa radio (SF7, BW500, 10dBm)
    // - 1F supercapacitor (1.8V-4.2V operating range)

    uint32_t nDevices = 10;
    double simulationTime = 3600; // 1 hour default
    double areaRadius = 810; // meters (0.81km range for SF7 from Semtech calculator)
    uint32_t energyScenario = CONSTANT_SOLAR;
    uint32_t discoveryProtocol = BEACON_BASED;

    // Supercapacitor energy storage
    // W_eff = 1/2 * C * (V_max² - V_min²)
    // C = 1F, V_max = 4.2V, V_min = 1.8V
    // W_eff = 0.5 * 1 * (17.64 - 3.24) = 7.2 Joules
    double initialEnergy = 7.2; // Joules

    double txPower = 10; // dBm (from Semtech calculator)
    double beaconInterval = 60; // seconds

    // Solar harvesting for regular artificial lighting (100-2000 lx)
    // Epishine LEH3_50x50_6: 50µW/cm² * 25cm² = 1.25mW = 0.00125W
    double harvestingRate = 0.00125; // Watts (1.25 mW)

    std::string outputFile = "results/energy_discovery.txt";

    CommandLine cmd;
    cmd.AddValue("nDevices", "Number of end devices", nDevices);
    cmd.AddValue("time", "Simulation time (s)", simulationTime);
    cmd.AddValue("radius", "Area radius (m) - 810m for SF7", areaRadius);
    cmd.AddValue("energyScenario", "0=None, 1=Regular(100-2000lx), 2=Day/Night, 3=LowLight(10-100lx), 4=Hybrid", energyScenario);
    cmd.AddValue("protocol", "0=Beacon, 1=ALOHA, 2=Scheduled, 3=Adaptive", discoveryProtocol);
    cmd.AddValue("initialEnergy", "Initial energy (J) - 7.2J for 1F supercap (1.8-4.2V)", initialEnergy);
    cmd.AddValue("txPower", "Transmission power (dBm) - 10dBm default", txPower);
    cmd.AddValue("beaconInterval", "Beacon interval (s)", beaconInterval);
    cmd.AddValue("harvestingRate", "Harvesting rate (W) - 0.00125W for regular light, 0.0000625W for low light", harvestingRate);
    cmd.AddValue("output", "Output file path", outputFile);
    cmd.Parse(argc, argv);

    // Print configuration
    std::cout << "\n========================================" << std::endl;
    std::cout << "LoRa Energy Harvesting & Discovery Simulation" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Hardware Configuration:" << std::endl;
    std::cout << "  Solar Cell: Epishine LEH3_50x50_6 (25 cm²)" << std::endl;
    std::cout << "  Radio: Semtech SX127X (SF7, BW500, CR4/7)" << std::endl;
    std::cout << "  Storage: 1F Supercapacitor (1.8-4.2V)" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Simulation Parameters:" << std::endl;
    std::cout << "  Devices: " << nDevices << std::endl;
    std::cout << "  Simulation time: " << simulationTime << " s (" << simulationTime/3600.0 << " h)" << std::endl;
    std::cout << "  Area radius: " << areaRadius << " m" << std::endl;

    const char* scenarioNames[] = {"No Harvesting", "Regular Light (100-2000 lx)",
                                    "Day/Night Cycle", "Low Light (10-100 lx)", "Hybrid"};
    std::cout << "  Energy scenario: " << scenarioNames[energyScenario] << std::endl;

    const char* protocolNames[] = {"Beacon-Based", "ALOHA Discovery",
                                    "Scheduled Listening", "Adaptive Discovery"};
    std::cout << "  Discovery protocol: " << protocolNames[discoveryProtocol] << std::endl;

    std::cout << "========================================" << std::endl;
    std::cout << "Energy Parameters:" << std::endl;
    std::cout << "  Initial energy: " << initialEnergy << " J" << std::endl;
    std::cout << "  TX power: " << txPower << " dBm" << std::endl;
    std::cout << "  TX energy: ~59.4 mJ per packet (20 bytes)" << std::endl;
    std::cout << "  RX power: 35.64 mW (10.8 mA @ 3.3V)" << std::endl;
    std::cout << "  Idle power: ~1 µW" << std::endl;
    std::cout << "  Harvesting rate: " << harvestingRate*1000 << " mW" << std::endl;
    std::cout << "  Beacon interval: " << beaconInterval << " s" << std::endl;
    std::cout << "========================================\n" << std::endl;

    // Create nodes
    NodeContainer endDevices;
    endDevices.Create(nDevices);
    NodeContainer gateways;
    gateways.Create(1);

    // Mobility - uniform disc distribution
    MobilityHelper mobility;
    mobility.SetPositionAllocator("ns3::UniformDiscPositionAllocator",
                                   "rho", DoubleValue(areaRadius),
                                   "X", DoubleValue(0.0),
                                   "Y", DoubleValue(0.0));
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(endDevices);

    // Gateway at center, elevated (15m)
    Ptr<ListPositionAllocator> gwAllocator = CreateObject<ListPositionAllocator>();
    gwAllocator->Add(Vector(0.0, 0.0, 15.0));
    mobility.SetPositionAllocator(gwAllocator);
    mobility.Install(gateways);

    std::cout << "✓ Created and positioned " << nDevices << " devices and 1 gateway" << std::endl;

    // LoRa channel with realistic propagation
    Ptr<LogDistancePropagationLossModel> loss = CreateObject<LogDistancePropagationLossModel>();
    loss->SetPathLossExponent(3.76);
    loss->SetReference(1, 7.7);

    Ptr<PropagationDelayModel> delay = CreateObject<ConstantSpeedPropagationDelayModel>();
    Ptr<LoraChannel> channel = CreateObject<LoraChannel>(loss, delay);

    // PHY and MAC helpers
    LoraPhyHelper phyHelper = LoraPhyHelper();
    phyHelper.SetChannel(channel);

    LorawanMacHelper macHelper = LorawanMacHelper();
    LoraHelper helper = LoraHelper();
    helper.EnablePacketTracking();

    // Install LoRa on end devices
    macHelper.SetDeviceType(LorawanMacHelper::ED_A);
    phyHelper.SetDeviceType(LoraPhyHelper::ED);
    NetDeviceContainer endDevicesNetDevices = helper.Install(phyHelper, macHelper, endDevices);

    // Install LoRa on gateway
    macHelper.SetDeviceType(LorawanMacHelper::GW);
    phyHelper.SetDeviceType(LoraPhyHelper::GW);
    helper.Install(phyHelper, macHelper, gateways);

    // Set spreading factors based on distance
    macHelper.SetSpreadingFactorsUp(endDevices, gateways, channel);

    std::cout << "✓ Configured LoRa network" << std::endl;

    // Energy model - realistic Semtech SX127X parameters
    BasicEnergySourceHelper energySourceHelper;
    energySourceHelper.Set("BasicEnergySourceInitialEnergyJ", DoubleValue(initialEnergy));
    EnergySourceContainer sources = energySourceHelper.Install(endDevices);

    // LoRa Radio Energy Model
    // Based on Semtech SX127X datasheet and calculator
    // SF7, BW500, CR4/7, 20 bytes payload, 10dBm:
    //   TX: 59.4 mJ per transmission (5µAh at 3.3V)
    //   RX: 10.8 mA at 3.3V = 35.64 mW
    //   Idle: ~1 µW
    LoraRadioEnergyModelHelper radioEnergyHelper;
    radioEnergyHelper.Set("StandbyCurrentA", DoubleValue(0.0003));       // ~1µW / 3.3V
    radioEnergyHelper.Set("TxCurrentA", DoubleValue(0.120));             // ~400mW for 10dBm
    radioEnergyHelper.Set("SleepCurrentA", DoubleValue(0.0000003));      // <1µW sleep
    radioEnergyHelper.Set("RxCurrentA", DoubleValue(0.0108));            // 10.8mA = 35.64mW

    radioEnergyHelper.Install(endDevicesNetDevices, sources);

    std::cout << "✓ Configured energy models" << std::endl;

    // Energy harvesting trackers
    std::vector<Ptr<EnergyHarvestingTracker>> harvesters;
    for (uint32_t i = 0; i < endDevices.GetN(); i++)
    {
        Ptr<EnergyHarvestingTracker> harvester = CreateObject<EnergyHarvestingTracker>();
        harvester->SetEnergySource(sources.Get(i));
        harvester->SetScenario((EnergyHarvestScenario)energyScenario);
        harvester->SetBaseRate(harvestingRate);
        harvester->Start();
        harvesters.push_back(harvester);

        // Initialize statistics
        nodeStatistics[i].nodeId = i;
        nodeStatistics[i].initialEnergy = initialEnergy;
    }

    if (energyScenario != NO_HARVESTING)
    {
        std::cout << "✓ Enabled energy harvesting (" << harvestingRate*1000 << " mW)" << std::endl;
    }

    // Discovery applications
    std::vector<Ptr<DiscoveryBeaconApp>> discoveryApps;
    for (uint32_t i = 0; i < endDevices.GetN(); i++)
    {
        Ptr<DiscoveryBeaconApp> app = CreateObject<DiscoveryBeaconApp>();
        app->SetProtocol((DiscoveryProtocol)discoveryProtocol);
        app->SetBeaconInterval(Seconds(beaconInterval));
        app->SetListenInterval(Seconds(beaconInterval / 2));
        endDevices.Get(i)->AddApplication(app);
        app->SetStartTime(Seconds(1.0));
        app->SetStopTime(Seconds(simulationTime));
        discoveryApps.push_back(app);
    }

    std::cout << "✓ Configured discovery protocol" << std::endl;

    // Periodic sender for normal LoRa traffic
    PeriodicSenderHelper periodicHelper;
    periodicHelper.SetPeriod(Seconds(300)); // Send data every 5 minutes
    ApplicationContainer apps = periodicHelper.Install(endDevices);
    apps.Start(Seconds(10));
    apps.Stop(Seconds(simulationTime));

    std::cout << "✓ Configured periodic data transmission (every 300s)" << std::endl;
    std::cout << "\n▶ Running simulation..." << std::endl;

    // Run simulation
    Simulator::Stop(Seconds(simulationTime));
    Simulator::Run();

    std::cout << "\n========================================" << std::endl;
    std::cout << "Simulation Results" << std::endl;
    std::cout << "========================================" << std::endl;

    // Collect and save statistics
    std::ofstream outFile(outputFile);
    outFile << "NodeID,InitialEnergy,FinalEnergy,Consumed,Harvested,BeaconsSent,BeaconsReceived,Discovered\n";

    double totalConsumed = 0.0;
    double totalHarvested = 0.0;
    uint32_t totalBeaconsSent = 0;
    uint32_t totalBeaconsReceived = 0;
    uint32_t discoveredNodes = 0;

    for (uint32_t i = 0; i < endDevices.GetN(); i++)
    {
        double finalEnergy = sources.Get(i)->GetRemainingEnergy();
        double consumed = initialEnergy - finalEnergy;
        double harvested = harvesters[i]->GetTotalHarvested();

        nodeStatistics[i].finalEnergy = finalEnergy;
        nodeStatistics[i].energyConsumed = consumed;
        nodeStatistics[i].energyHarvested = harvested;
        nodeStatistics[i].beaconsSent = discoveryApps[i]->GetBeaconsSent();
        nodeStatistics[i].beaconsReceived = discoveryApps[i]->GetBeaconsReceived();
        nodeStatistics[i].discovered = (nodeStatistics[i].beaconsReceived > 0);

        totalConsumed += consumed;
        totalHarvested += harvested;
        totalBeaconsSent += nodeStatistics[i].beaconsSent;
        totalBeaconsReceived += nodeStatistics[i].beaconsReceived;
        if (nodeStatistics[i].discovered) discoveredNodes++;

        // Node position
        Ptr<MobilityModel> mob = endDevices.Get(i)->GetObject<MobilityModel>();
        Vector pos = mob->GetPosition();
        double distance = sqrt(pos.x * pos.x + pos.y * pos.y);

        std::cout << "\nNode " << i << ":" << std::endl;
        std::cout << "  Position: (" << pos.x << ", " << pos.y << ") m" << std::endl;
        std::cout << "  Distance from GW: " << distance << " m" << std::endl;
        std::cout << "  Initial energy: " << initialEnergy << " J" << std::endl;
        std::cout << "  Final energy: " << finalEnergy << " J ("
                  << (finalEnergy/initialEnergy*100) << "%)" << std::endl;
        std::cout << "  Consumed: " << consumed << " J" << std::endl;
        std::cout << "  Harvested: " << harvested << " J" << std::endl;
        std::cout << "  Net balance: " << (harvested - consumed) << " J" << std::endl;
        std::cout << "  Beacons sent: " << nodeStatistics[i].beaconsSent << std::endl;
        std::cout << "  Beacons received: " << nodeStatistics[i].beaconsReceived << std::endl;
        std::cout << "  Discovered: " << (nodeStatistics[i].discovered ? "Yes" : "No") << std::endl;

        outFile << i << ","
                << initialEnergy << ","
                << finalEnergy << ","
                << consumed << ","
                << harvested << ","
                << nodeStatistics[i].beaconsSent << ","
                << nodeStatistics[i].beaconsReceived << ","
                << (nodeStatistics[i].discovered ? 1 : 0) << "\n";
    }

    outFile.close();

    // Summary statistics
    std::cout << "\n========================================" << std::endl;
    std::cout << "Summary Statistics" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Total nodes: " << nDevices << std::endl;
    std::cout << "Discovered nodes: " << discoveredNodes << " ("
              << (discoveredNodes*100.0/nDevices) << "%)" << std::endl;
    std::cout << "Average energy consumed: " << (totalConsumed/nDevices) << " J" << std::endl;
    std::cout << "Average energy harvested: " << (totalHarvested/nDevices) << " J" << std::endl;
    std::cout << "Average net balance: " << ((totalHarvested-totalConsumed)/nDevices) << " J" << std::endl;
    std::cout << "Total beacons sent: " << totalBeaconsSent << std::endl;
    std::cout << "Total beacons received: " << totalBeaconsReceived << std::endl;
    std::cout << "Average beacons per node: " << (totalBeaconsSent*1.0/nDevices) << std::endl;

    // Packet tracker statistics
    LoraPacketTracker& tracker = helper.GetPacketTracker();
    std::cout << "\n" << tracker.CountMacPacketsGlobally(Seconds(0), Seconds(simulationTime)) << std::endl;

    // Energy sustainability analysis
    double avgNetBalance = (totalHarvested - totalConsumed) / nDevices;
    double hoursOfOperation = simulationTime / 3600.0;
    double projectedLifetime = 0.0;

    if (avgNetBalance >= 0)
    {
        std::cout << "\n✓ Energy-positive operation (sustainable)" << std::endl;
        std::cout << "  Average surplus: " << avgNetBalance << " J over "
                  << hoursOfOperation << " hours" << std::endl;
    }
    else
    {
        double avgConsumptionRate = totalConsumed / nDevices / simulationTime; // J/s
        double avgHarvestingRate = totalHarvested / nDevices / simulationTime; // J/s
        double netConsumptionRate = avgConsumptionRate - avgHarvestingRate;
        if (netConsumptionRate > 0)
        {
            projectedLifetime = initialEnergy / netConsumptionRate / 3600.0; // hours
            std::cout << "\n⚠ Energy-negative operation (not sustainable)" << std::endl;
            std::cout << "  Average deficit: " << -avgNetBalance << " J over "
                      << hoursOfOperation << " hours" << std::endl;
            std::cout << "  Projected lifetime: " << projectedLifetime << " hours" << std::endl;
        }
    }

    std::cout << "\n✓ Results saved to: " << outputFile << std::endl;
    std::cout << "========================================\n" << std::endl;

    Simulator::Destroy();
    return 0;
}
