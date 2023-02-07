"""Constants for the SolarEdge Optimizers Data integration."""
from datetime import timedelta
import logging

DOMAIN = "solaredgeoptimizers"
CONF_SITE_ID = "siteid"
DATA_API_CLIENT = "api_client"

PANEEL_DATA = "paneel_data"

LOGGER = logging.getLogger(__package__)

UPDATE_DELAY = timedelta(minutes=15)

CHECK_TIME_DELTA = timedelta(hours=1, minutes=00)

SENSOR_TYPE_CURRENT = "Current"
SENSOR_TYPE_OPT_VOLTAGE = "Optimizer_voltage"
SENSOR_TYPE_POWER = "Power"
SENSOR_TYPE_VOLTAGE = "Voltage"
SENSOR_TYPE_ENERGY = "Lifetime_energy"
SENSOR_TYPE_LASTMEASUREMENT = "Last_Measurement"
SENSOR_TYPE = [
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_OPT_VOLTAGE,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_VOLTAGE,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_LASTMEASUREMENT,
]
