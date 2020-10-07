# recipe_setter_server

A flask server to monitor a production line.

Allows an Android tablet to set a recipe for a production line using the DigitME RecipeSetter app. RFID antennas at the start and end of the line monitor the movement of trays along the line, updating a database accordingly.

Exposes /get_status, /recipe_options and /change_recipe for use with the Android app.

Accepts POST requests to /rfid when an accompanying RFID kit picks up a tag. These are currently sent using Speedway Connect.
Example of an RFID request:
[
   {
      "antennaPort":2,
      "epc":"E20041026708007026400EA0",
      "userMemory":"",
      "tid":"E20034120138F40005F20EA0",
      "isHeartBeat":False
   },
   {
      "antennaPort":2,
      "epc":"E20041026708007026400EA0",
      "userMemory":"0000000000000000000000000000000000000000",
      "tid":"E20034120138F40005F20EA0",
      "isHeartBeat":False
   },
   {
      "antennaPort":2,
      "epc":"E20041026708007026100E9D",
      "userMemory":"0000000000000000000000000000000000000000",
      "tid":"E20034120130F40005F20E9D",
      "isHeartBeat":False
   }
]
