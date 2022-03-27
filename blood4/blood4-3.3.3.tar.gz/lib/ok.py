def ok():
    print("""
    
    #include "ns3/core-module.h"
    #include "ns3/point-to-point-module.h"
    #include "ns3/network-module.h"
    #include "ns3/applications-module.h"
    #include "ns3/wifi-module.h"
    #include "ns3/mobility-module.h"
    #include "ns3/internet-module.h"
    
    using namespace ns3;
    
    int
    main (int argc, char *argv[])
    {
      
      CommandLine cmd;
      cmd.Parse (argc,argv);
    
      LogComponentEnable ("UdpEchoClientApplication", LOG_LEVEL_INFO);
      LogComponentEnable ("UdpEchoServerApplication", LOG_LEVEL_INFO);
    
      NodeContainer p2pNodes;
      p2pNodes.Create (2);
    
      PointToPointHelper pointToPoint;
      pointToPoint.SetDeviceAttribute ("DataRate", StringValue ("5Mbps"));
      pointToPoint.SetChannelAttribute ("Delay", StringValue ("2ms"));
    
      NetDeviceContainer p2pDevices;
      p2pDevices = pointToPoint.Install (p2pNodes);
    
      NodeContainer wifiStaNodes;
      wifiStaNodes.Create (3);
      NodeContainer wifiApNode = p2pNodes.Get (0);
    
      YansWifiChannelHelper channel = YansWifiChannelHelper::Default ();
      YansWifiPhyHelper phy = YansWifiPhyHelper::Default ();
      phy.SetChannel (channel.Create ());
    
      WifiHelper wifi;
      wifi.SetRemoteStationManager ("ns3::AarfWifiManager");
    
      WifiMacHelper mac;
      Ssid ssid = Ssid ("ns-3-ssid");
      mac.SetType ("ns3::StaWifiMac",
                   "Ssid", SsidValue (ssid),
                   "ActiveProbing", BooleanValue (false));
    
      NetDeviceContainer staDevices;
      staDevices = wifi.Install (phy, mac, wifiStaNodes);
    
      mac.SetType ("ns3::ApWifiMac",
                   "Ssid", SsidValue (ssid));
    
      NetDeviceContainer apDevices;
      apDevices = wifi.Install (phy, mac, wifiApNode);
    
      MobilityHelper mobility;
    
      mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                     "MinX", DoubleValue (10.0),
                                     "MinY", DoubleValue (-10.0),
                                     "DeltaX", DoubleValue (7.0),
                                     "DeltaY", DoubleValue (12.0),
                                     "GridWidth", UintegerValue (2),
                                     "LayoutType", StringValue ("RowFirst"));
    
      mobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel",
                                 "Bounds", RectangleValue (Rectangle (-50, 50, -50, 50)));
      mobility.Install (wifiStaNodes);
    
      mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
      mobility.Install (wifiApNode);
    
      InternetStackHelper stack;
      stack.Install (p2pNodes.Get(1));
      stack.Install (wifiApNode);
      stack.Install (wifiStaNodes);
    
      Ipv4AddressHelper address;
    
      address.SetBase ("10.1.1.0", "255.255.255.0");
      Ipv4InterfaceContainer p2pInterfaces;
      p2pInterfaces = address.Assign (p2pDevices);
    
      address.SetBase ("10.1.3.0", "255.255.255.0");
      address.Assign (staDevices);
      address.Assign (apDevices);
    
      UdpEchoServerHelper echoServer (9);
    
      ApplicationContainer serverApps = echoServer.Install (p2pNodes.Get (1));
      serverApps.Start (Seconds (1.0));
      serverApps.Stop (Seconds (10.0));
    
      UdpEchoClientHelper echoClient (p2pInterfaces.GetAddress (1), 9);
      echoClient.SetAttribute ("MaxPackets", UintegerValue (1));
      echoClient.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
      echoClient.SetAttribute ("PacketSize", UintegerValue (1024));
    
      ApplicationContainer clientApps = echoClient.Install (wifiStaNodes.Get (2));
      clientApps.Start (Seconds (2.0));
      clientApps.Stop (Seconds (10.0));
    
      Ipv4GlobalRoutingHelper::PopulateRoutingTables ();
    
      Simulator::Stop (Seconds (10.0));
    
      AsciiTraceHelper ascii;
      pointToPoint.EnableAsciiAll (ascii.CreateFileStream ("Tracefilewif.tr"));
      phy.EnableAsciiAll (ascii.CreateFileStream ("Tracefilephy.tr"));
      
      Simulator::Run ();
      Simulator::Destroy ();
      return 0;
    }

    """)