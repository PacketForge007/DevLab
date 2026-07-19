/interface bridge add name=bridge
/interface vlan add interface=bridge name="vlan100-MGMT" vlan-id=100
/interface vlan add interface=bridge name="vlan200-USER" vlan-id=200
/interface list add name=WAN
/interface list add name=LAN
/ip pool add name=MGMT-Pool ranges=10.192.12.1-10.192.12.10
/ip pool add name=User-Pool ranges=192.168.12.11-192.168.13.254
/ip dhcp-server add address-pool=MGMT-Pool disabled=no interface="vlan100-MGMT" lease-time=1h name=dhcp1-MGMT
/ip dhcp-server add address-pool=User-Pool disabled=no interface="vlan200-USER" lease-time=1h name=dhcp2-Users
/interface bridge port add bridge=bridge interface=ether4
/interface bridge port add bridge=bridge interface=ether5
/ip neighbor discovery-settings set discover-interface-list=LAN
/interface list member add interface=bridge list=LAN
/interface list member add interface=ether1 list=WAN
#/ip address add address=[WAN-IP/Prefix] interface=ether1 network=[Network-Address]
/ip address add address=10.192.12.14/28 interface="vlan100-MGMT" network=10.192.12.0
/ip address add address=192.168.12.1/23 interface="vlan200-USER" network=192.168.12.0
/ip dhcp-server network add address=10.192.12.0/28 dns-server=8.8.8.8,4.2.2.2 gateway=10.192.12.14
/ip dhcp-server network add address=192.168.12.0/23 dns-server=8.8.8.8,4.2.2.2 gateway=192.168.12.1
/ip firewall filter add action=accept chain=input dst-port=8291 protocol=tcp
/ip firewall filter add action=accept chain=input comment="defconf: accept established,related,new,untracked" connection-state=established,related,new,untracked
/ip firewall filter add action=drop chain=input comment="defconf: drop invalid" connection-state=invalid
/ip firewall filter add action=accept chain=input comment="defconf: accept ICMP" protocol=icmp
/ip firewall filter add action=accept chain=input comment="defconf: accept to local loopback (for CAPsMAN)" dst-address=127.0.0.1
/ip firewall filter add action=drop chain=input comment="defconf: drop all not coming from LAN" in-interface-list=!LAN
/ip firewall filter add action=accept chain=forward comment="defconf: accept in ipsec policy" ipsec-policy=in,ipsec
/ip firewall filter add action=accept chain=forward comment="defconf: accept out ipsec policy" ipsec-policy=out,ipsec
/ip firewall filter add action=fasttrack-connection chain=forward comment="defconf: fasttrack" connection-state=established,related
/ip firewall filter add action=accept chain=forward comment="defconf: accept established,related, untracked" connection-state=established,related,untracked
/ip firewall filter add action=drop chain=forward comment="defconf: drop invalid" connection-state=invalid
/ip firewall filter add action=drop chain=forward comment="defconf: drop all from WAN not DSTNATed" connection-nat-state=!dstnat connection-state=new in-interface-list=WAN
/ip firewall nat add action=masquerade chain=srcnat ipsec-policy=out,none out-interface-list=WAN
#/ip route
#add distance=1 gateway=[WAN-GW]
/user add name=amit group=full password=Qwerty#123
/ip service set api disabled=yes
/ip service set api-ssl disabled=yes
/ip service set ftp disabled=yes
/ip service set telnet disabled=yes
/ip service set www disabled=yes
/ip service set www-ssl disabled=yes
/system clock set time-zone-name=Asia/Kolkata
/ip dns set servers=8.8.8.8,4.2.2.2
/ip dns set allow-remote-requests=yes
/interface set ether1 name=ether1-WAN
/interface set ether4 name=ether4-LAN
/interface set ether5 name=ether5-LAN
quit