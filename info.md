# SolarEdge Optimizers Data
Intergration to get optimizers information from the SolarEdge portal

This intergrations works by gathering the information from the SolarEdge portal website. The current data per optimizer is gather and show in HomeAssistant. Also is the total energy produced per optimizer added as sensor.
For this intergration to work you need to provide it with your information: your Site-id, your username and password.

Tis intergration will update its sensors every 15 min. More frequant is not usefull beacsuse the portal will only update that much.

When the inverter is not working, the last know result is send back from the portal. The intergation will check if the value for last measerement is less then 1 hour. If not, meaning the inverter is offline, the value for all sensors (except Last measerement and total energy produced) will be set to 0. 

# Installation
The best method is using HACS (https://hacs.xyz)
1.  Make sure you have hacs installed
2.  Add this repository as custom repository to hacs by going to hacs, integrations, click on the three dots in the upper right corner and click on custom repositories.
3.  In the repository field, fill in the link to this repository (https://github.com/ProudElm/solaredgeoptimizers) and for category, select Integration. Click on Add
4.  Go back to hacs, integrations and add click on the blue button Exlore and download repositories in the bottom left corner, search for SolarEdge Optimizers Data and install it
5.  Reboot HA
6.  In HA goto Config -> Integrations. Add the SolarEdge Optimizers Data to HA.
7.  Enter your Site-ID, username and password.

The initial setup can take some time, please be patient.
