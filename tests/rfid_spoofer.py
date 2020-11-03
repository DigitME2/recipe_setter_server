import os
import sys
import time

import requests

rfid = os.environ.get('RFID') or "test_rfid_epc2"
try:
    antenna_port = sys.argv[1]
except:
    print("Enter the antenna port number as an argument e.g. \"python rfid_spoofer.py 1\"")
    exit()

url = "http://localhost:8080/rfid"
post_json = {"tag_reads": [{"antennaPort": antenna_port, "epc": rfid}]}
while True:
    x = requests.post(url, json=post_json)
    print(x)
    time.sleep(5)

    #"E20041026708007026100E9D"