from os import error, system
from sys import stderr, stdin, stdout
import subprocess
import paramiko; import pwinput
from time import sleep
import ipaddress


print("\n\n\n", """
██╗░░██╗░█████╗░░██████╗░  ██████╗░████████╗██████╗░  ░██████╗░█████╗░██████╗░██╗██████╗░████████╗
██║░██╔╝██╔══██╗██╔════╝░  ██╔══██╗╚══██╔══╝██╔══██╗  ██╔════╝██╔══██╗██╔══██╗██║██╔══██╗╚══██╔══╝
█████═╝░██║░░╚═╝██║░░██╗░  ██████╔╝░░░██║░░░██████╔╝  ╚█████╗░██║░░╚═╝██████╔╝██║██████╔╝░░░██║░░░
██╔═██╗░██║░░██╗██║░░╚██╗  ██╔══██╗░░░██║░░░██╔══██╗  ░╚═══██╗██║░░██╗██╔══██╗██║██╔═══╝░░░░██║░░░
██║░╚██╗╚█████╔╝╚██████╔╝  ██║░░██║░░░██║░░░██║░░██║  ██████╔╝╚█████╔╝██║░░██║██║██║░░░░░░░░██║░░░
╚═╝░░╚═╝░╚════╝░░╚═════╝░  ╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝  ╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝╚═╝░░░░░░░░╚═╝░░░""", "\n\n\n")


t = 0

while t < 3:

    try:
        mkt = str(ipaddress.ip_address(input("\nMIKROTIK IPv4: ")))
        break
    except ValueError:
        print("\n!!!Invalid IP Address. Please try again !!!\n")
        t += 1
        if t == 3:
            exit()
        continue

# Pinging the IP to check connectivity:

print(f"\n\nPinging {mkt}.....", "\n")

pn = subprocess.run(['ping', mkt], capture_output=True)
out = pn.stdout.decode()
print(out)

if f"Reply from {mkt}" in out:
    status = f"\n{mkt} is UP"
    print(status, "\n")
else:
    status = f"\n{mkt} is Down"
    print(status, "\n")
    system('pause\n')
    exit() # If Down, Exit out of the code
sleep(2)


#input for Mikrotik Credentials:

print("\n\n!!! USERNAME AND PASSWORD MUST BE CONFIGURED IN THE ROUTER TO GO FURTHER !!!\n")

user = str(input("\nUsername [default: admin]: ")) or "admin"
passwd = str(pwinput.pwinput(prompt ="\nPassword [default: admin]: ", mask="*")) or "admin"

ntwk_id = int(input("\n\nProvide LAN-NTWK-ID i.e. 10.192.X.0:-> "))

print("\nMGMT Network prefix is set to default /28\n")

ntwk_prefix = str(input("\nProvide User-Network Prefix. i.e. /23 or /24:-> "))

ntp1 = "/system ntp client set enabled=yes mode=unicast servers=0.in.pool.ntp.org"

ntp2 = "/system ntp client set enabled=yes server-dns-names=0.in.pool.ntp.org"

script=f"""/interface bridge add name=bridge
/interface vlan add interface=bridge name="vlan100-MGMT" vlan-id=100
/interface vlan add interface=bridge name="vlan200-USER" vlan-id=200
/interface list add name=WAN
/interface list add name=LAN
/ip pool add name=MGMT-Pool ranges=10.192.{ntwk_id}.1-10.192.{ntwk_id}.10
/ip pool add name=User-Pool ranges=192.168.{ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}.11-192.168.{ntwk_id+1 if (ntwk_id%2)==0 and ntwk_prefix=="/23" else ntwk_id}.254
/ip dhcp-server add address-pool=MGMT-Pool disabled=no interface="vlan100-MGMT" lease-time=1h name=dhcp1-MGMT
/ip dhcp-server add address-pool=User-Pool disabled=no interface="vlan200-USER" lease-time=1h name=dhcp2-Users
/interface bridge port add bridge=bridge interface=ether4
/interface bridge port add bridge=bridge interface=ether5
/ip neighbor discovery-settings set discover-interface-list=LAN
/interface list member add interface=bridge list=LAN
/interface list member add interface=ether1 list=WAN
#/ip address add address=[WAN-IP/Prefix] interface=ether1 network=[Network-Address]
/ip address add address=10.192.{ntwk_id}.14/28 interface="vlan100-MGMT" network=10.192.{ntwk_id}.0
/ip address add address=192.168.{ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}.1{ntwk_prefix} interface="vlan200-USER" network=192.168.{ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}.0
/ip dhcp-server network add address=10.192.{ntwk_id}.0/28 dns-server=8.8.8.8,4.2.2.2 gateway=10.192.{ntwk_id}.14
/ip dhcp-server network add address=192.168.{ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}.0{ntwk_prefix} dns-server=8.8.8.8,4.2.2.2 gateway=192.168.{ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}.1
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
quit"""

#create a txt file of modified script:

f = open("KCG_Router_Script.rsc", "w")
f.write(script)
f.close
print('\n\nFile "KCG_RTR_Script.rsc" created at current directory for reference...\n\n')


# SSH Connection to the Router:

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#connect to the router:

ssh.connect(mkt, username=user, password=passwd)

sleep(2)
print(f"Configuring {mkt}......", "\n")
sleep(2)

#execute the script:
stdin, stdout, stderr = ssh.exec_command("/system resource print")
ver = stdout.read().decode('utf-8')

if "version: 7." in ver:
    stdin, stdout, stderr = ssh.exec_command(ntp1)
    stdin.close()
    stdout.close()
    stderr.close()

else:
    stdin, stdout, stderr = ssh.exec_command(ntp2)
    stdin.close()
    stdout.close()
    stderr.close()

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode('utf-8')
print(output.replace("interrupted", ""))

if ("failure" or "ambiguous" or "no such item") in output:
    try:
        raise error()
    except error:
        print(f"\nCommand Failed for {mkt}. Please check manually !!!\n\n")
        system('pause\n')
        exit()
elif "interrupted" in output:
    print("!!! Script Executed Successfully !!!", "\n\n")

if stderr:
    for line in stderr:
        print(line)

stdin.close()
stdout.close()
stderr.close()
ssh.close

system('pause\n')
