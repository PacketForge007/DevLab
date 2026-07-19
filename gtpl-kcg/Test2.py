from sys import stderr, stdin, stdout
import paramiko; import pwinput
from time import sleep

mkt=input("Provide Mikrotik IP: ")
user=input("Username: ")
passwd = pwinput.pwinput(prompt ="Password: ", mask="*")


print()
ntwk_id=int(input("Provide LAN-NTWK-ID i.e. 10.192.X.0:-> "))
print("\n")

print("MGMT Network prefix is set to default /28")
print("\n")

ntwk_prefix=input("Provide User-Network Prefix. i.e. /23 or /24:-> ")
print("\n")


script=f"""/interface bridge
add name=bridge
/interface vlan
add interface=bridge name="vlan100-MGMT" vlan-id=100
add interface=bridge name="vlan200-USER" vlan-id=200
/interface list
add name=WAN
add name=LAN
/ip pool
add name=MGMT-Pool ranges=10.192.{ntwk_id}.1-10.192.{ntwk_id}.10
add name=User-Pool ranges=192.168.{ntwk_id}.11-192.168.{ntwk_id+1 if ntwk_prefix=="/23" else ntwk_id}.254
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
add address=10.192.{ntwk_id}.14/28 interface="vlan100-MGMT" network=10.192.{ntwk_id}.0
add address=192.168.{ntwk_id}.1{ntwk_prefix} interface="vlan200-USER" network=192.168.{ntwk_id}.0
/ip dhcp-server network
add address=10.192.{ntwk_id}.0/28 dns-server=8.8.8.8,4.2.2.2 gateway=10.192.{ntwk_id}.14
add address=192.168.{ntwk_id}.0{ntwk_prefix} dns-server=8.8.8.8,4.2.2.2 gateway=192.168.{ntwk_id}.1
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

sleep(8)

# print(script)

#SSH Connection to the Router:

ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#connect to the router:

ssh.connect(mkt, username=user, password=passwd)

#configure IP address on an interface

# int_name="ether2"
# ip_add="192.168.1.1/24"
# command=f'/ip address add address={ip_add} interface={int_name}'
stdin, stdout, stderr = ssh.exec_command(".//KCG_Router_Script.rsc")
output = stdout.read().decode('utf-8')
stdin.close()
stdout.close()
stderr.close()

print(output)

ssh.close

