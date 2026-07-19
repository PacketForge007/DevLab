# ntwk_id = int(input("Privide Network ID: "))
# ntwk_prefix = input("Provide Network Prefix: ")

# # ntwk_id if ((ntwk_id%2==0 or ntwk_id%2!=0) and (ntwk_prefix=="/24" or ntwk_prefix=="/23")) else ntwk_id-1

# ntwk_id = {ntwk_id-1 if ntwk_id%2!=0 and ntwk_prefix=="/23" else ntwk_id}

# print(ntwk_id, ntwk_prefix)


# from os import system

# system('pause')

import logging

logging.basicConfig(filename='k.logs', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


mkt = logging.info(input("MIKROTIK IP: "))

# print("\n\n!!! USERNAME AND PASSWORD MUST BE CONFIGURED IN THE ROUTER TO GO FURTHER !!!\n")
# logging.info("\n\n!!! USERNAME AND PASSWORD MUST BE CONFIGURED IN THE ROUTER TO GO FURTHER !!!\n".replace("\n", ""))