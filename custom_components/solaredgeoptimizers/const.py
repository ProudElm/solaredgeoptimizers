"""Constants for the SolarEdge Optimizers Data integration."""
from datetime import timedelta
import logging

# from datetime import timedelta


DOMAIN = "solaredgeoptimizers"
CONF_SITE_ID = "siteid"
DATA_API_CLIENT = "api_client"

PANEEL_DATA = "paneel_data"

LOGGER = logging.getLogger(__package__)

UPDATE_DELAY = timedelta(minutes=15)

# SENSOR_TYPE = ["current", "optimizer_voltage", "power", "voltage"]
SENSOR_TYPE_CURRENT = "Current"
SENSOR_TYPE_OPT_VOLTAGE = "Optimizer_voltage"
SENSOR_TYPE_POWER = "Power"
SENSOR_TYPE_VOLTAGE = "Voltage"
SENSOR_TYPE_ENERGY = "Lifetime_energy"
SENSOR_TYPE = [
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_OPT_VOLTAGE,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_VOLTAGE,
    SENSOR_TYPE_ENERGY,
]
