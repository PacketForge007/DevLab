
## MGMT-IP Pools Range##
print()
mgmt_pool=input("Provide MGMT_Pool Range: ")
print()
mgmt_gw=input("Provide MGMT_GW with prefix. i.e. 10.192.1.14/28: ")
print()
mgmt_ntwk=input("Provide MGMT_NTWK Address. i.e. 10.192.1.0: ")
print()

## USER-IP Pools Range##

user_pool=input("Provide USER_Pool Range: ")
print()
user_gw=input("Provide USER_GW with prefix. i.e. 192.168.1.1/24: ")
print()
user_ntwk=input("Provide USER_NTWK Address. i.e. 192.168.1.0: ")
print()

## DHCP-Server Configs ##

dhcp_dns1, dhcp_dns2=input("Provide two dns IP [Default 8.8.8.8 4.2.2.2]: ") or None, None
print()
if dhcp_dns1 == None and dhcp_dns2 == None:
    dhcp_dns1, dhcp_dns2="8.8.8.8", "4.2.2.2"

dhcp_mgmt_gw=mgmt_gw.split("/")
print()
dhcp_user_gw=user_gw.split("/")
print()
dhcp_mgmt_ntwk=mgmt_ntwk+"/"+mgmt_gw.split("/")[1]
dhcp_user_ntwk=user_ntwk+"/"+user_gw.split("/")[1]


script=f"""/interface bridge
add name=bridge
/interface vlan
add interface=bridge name="vlan100-MGMT" vlan-id=100
add interface=bridge name="vlan200-USER" vlan-id=200
/interface list
add name=WAN
add name=LAN
/ip pool
add name=MGMT-Pool ranges={mgmt_pool}
add name=User-Pool ranges={user_pool}
/ip dhcp-server
add address-pool=MGMT-Pool disabled=no interface="vlan100-MGMT" lease-time=1h name=dhcp1-MGMT
add address-pool=User-Pool disabled=no interface="vlan200-USER" lease-time=1h name=dhcp2-Users
/interface bridge port
add bridge=bridge interface=ether4
add bridge=bridge interface=ether5
/ip neighbor discovery-settings
set discover-interface-list=LAN
/interface list member
add interface=bridge list=LAN
add interface=ether1 list=WAN
/ip address
#add address=[WAN-IP/Prefix] interface=ether1 network=[Network-Address]
add address={mgmt_gw} interface="vlan100-MGMT" network={mgmt_ntwk}
add address={user_gw} interface="vlan200-USER" network={user_ntwk}
/ip dhcp-server network
add address={dhcp_mgmt_ntwk} dns-server={dhcp_dns1},{dhcp_dns2} gateway={dhcp_mgmt_gw[0]}
add address={dhcp_user_ntwk} dns-server={dhcp_dns1},{dhcp_dns2} gateway={dhcp_user_gw[0]}
/ip firewall filter
add action=accept chain=input dst-port=8291 protocol=tcp
add action=accept chain=input comment="defconf: accept established,related,new,untracked" connection-state=established,related,new,untracked
add action=drop chain=input comment="defconf: drop invalid" connection-state=invalid
add action=accept chain=input comment="defconf: accept ICMP" protocol=icmp
add action=accept chain=input comment="defconf: accept to local loopback (for CAPsMAN)" dst-address=127.0.0.1
add action=drop chain=input comment="defconf: drop all not coming from LAN" in-interface-list=!LAN
add action=accept chain=forward comment="defconf: accept in ipsec policy" ipsec-policy=in,ipsec
add action=accept chain=forward comment="defconf: accept out ipsec policy" ipsec-policy=out,ipsec
add action=fasttrack-connection chain=forward comment="defconf: fasttrack" connection-state=established,related
add action=accept chain=forward comment="defconf: accept established,related, untracked" connection-state=established,related,untracked
add action=drop chain=forward comment="defconf: drop invalid" connection-state=invalid
add action=drop chain=forward comment="defconf: drop all from WAN not DSTNATed" connection-nat-state=!dstnat connection-state=new in-interface-list=WAN
/ip firewall nat
add action=masquerade chain=srcnat ipsec-policy=out,none out-interface-list=WAN
#/ip route
#add distance=1 gateway=[WAN-GW]
/user
add name=amit group=full password=Qwerty#123
/ip service
set api disabled=yes
set api-ssl disabled=yes
set ftp disabled=yes
set telnet disabled=yes
set www disabled=yes
set www-ssl disabled=yes
/system clock
set time-zone-name=Asia/Kolkata
/ip dns
set servers=8.8.8.8,4.2.2.2
set allow-remote-requests=yes
/system ntp client
set enabled=yes server-dns-names=0.in.pool.ntp.org
/interface set ether1 name=ether1-WAN
/interface set ether4 name=ether4-LAN
/interface set ether5 name=ether5-LAN
/

"""

f = open("KCG_Router_Script.rsc", "w")
f.write(script)
f.close
print()

print(script)

