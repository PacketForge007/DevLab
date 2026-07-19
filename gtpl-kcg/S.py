import paramiko
import pwinput
import subprocess
from time import sleep

with open('S.csv', encoding='utf-8-sig') as file:
    content = file.readlines()
# header = content[:1]
ips = content[:]
# print(header)
# print(rows)

ntp1 = "/system ntp client set enabled=yes mode=unicast servers=0.in.pool.ntp.org"

ntp2 = "/system ntp client set enabled=yes server-dns-names=0.in.pool.ntp.org"

for ip in ips:
    # print(row.replace("\n", ""))

    mkt = ip.replace("\n", "")
    user = input("\nUsername [default: admin]: ") or "admin"
    passwd = pwinput.pwinput(prompt ="\nPassword [default: admin]: ", mask="*") or "admin"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Pinging the IP to check connectivity:

    print(f"\n\nPinging {mkt}.....", "\n")

    pn = subprocess.run(['ping', mkt], capture_output=True)

    pnout = pn.stdout.decode()

    print(pnout, "\n")

    if f"Reply from {mkt}" in pnout:
        status = f"{mkt} is UP"
        print(status, "\n")
    else:
        status = f"{mkt} is Down"
        print(status, "\n")
        # exit() # If Down, Exit out of the code
        continue


    #connect to the router:

    ssh.connect(mkt, username=user, password=passwd)

    print(f"Configuring {mkt}......", "\n")
    sleep(3)

    stdin, stdout, stderr = ssh.exec_command("/system resource print")
    ver = stdout.read().decode('utf-8')

    if "version: 7." in ver:
        stdin, stdout, stderr = ssh.exec_command(ntp1)

    else:
        stdin, stdout, stderr = ssh.exec_command(ntp2)

    # print(output, "\n")

    # if "version: 7." in output:
    #     upgraded = True
    #     print(upgraded)

    # elif "version: 6." in output:
    #     upgraded = False
    #     print(upgraded)


    # if "interrupted" in output:

    # sleep(5)

    print(f"!!! Script Executed Successfully for {mkt} !!!", "\n")

    stdin.close()
    stdout.close()
    stderr.close()

    ssh.close

