import os

import requests

antenna_port = os.environ.get('ANTENNA') or 1
rfid = os.environ.get('RFID') or "E20041026708007026100E9D"

url = "http://localhost:5000/rfid"
json1 = {"tag_reads": [{"antennaPort": antenna_port, "epc": rfid}]}
x = requests.post(url, json=json1)
print(x)