# solaredgeoptimizers
Intergration to get optimizers information from the SolarEdge portal

This intergrations works by gathering the information from the SolarEdge portal website. The current data per optimizer is gather and show in HomeAssistant. Also is the total energy produced per optimizer added as sensor.
For this intergration to work you need to provide it with your information: your Site-id, your username and password.

Tis intergration will update its sensors every 15 min. More frequant is not usefull beacsuse the portal will only update that much.

When the inverter is not working, the last know result is send back from the portal. The intergation will check if the value for last measerement is less then 1 hour. If not, meaning the inverter is offline, the value for all sensors (except Last measerement and total energy produced) will be set to 0. 
