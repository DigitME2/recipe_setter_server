import os
import sys

import requests

rfid = os.environ.get('RFID') or "E20041026708007026100E9D"
try:
    antenna_port = sys.argv[1]
except:
    print("Enter the antenna port number as an argument e.g. \"python rfid_spoofer.py 1\"")
    exit()

url = "http://localhost:8080/rfid"
post_json = {"tag_reads": [{"antennaPort": antenna_port, "epc": rfid}]}
x = requests.post(url, json=post_json)
print(x)