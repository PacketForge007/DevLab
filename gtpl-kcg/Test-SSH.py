from sys import stderr, stdin, stdout
import paramiko; import pwinput

mkt=input("Provide Mikrotik IP: ")
user=input("Username: ")
passwd = pwinput.pwinput(prompt ="Password: ", mask="*")

ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#connect to the router:

ssh.connect(mkt, username=user, password=passwd)

#configure IP address on an interface

int_name="ether2"
ip_add="192.168.1.1/24"
command=f'/ip address add address={ip_add} interface={int_name}'
stdin, stdout, stderr = ssh.exec_command(command)
output = stdout.read().decode('utf-8')
stdin.close()
stdout.close()
stderr.close()

print(output)

ssh.close

