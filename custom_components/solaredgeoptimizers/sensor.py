"""Platform for sensor integration."""
from homeassistant.helpers.entity import DeviceInfo
import json

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.const import (
    POWER_WATT,
    ELECTRIC_POTENTIAL_VOLT,
    ELECTRIC_CURRENT_AMPERE,
    ENERGY_KILO_WATT_HOUR,
)

from .solaredgeoptimizers import (
    SolarEdgeOptimizerData,
    solaredgeoptimizers,
    SolarEdgeSite,
    SolarEdgeInverter,
    SolarEdgeString,
    SolarlEdgeOptimizer,
)
from .const import (
    DATA_API_CLIENT,
    DOMAIN,
    UPDATE_DELAY,
    SENSOR_TYPE,
    SENSOR_TYPE_OPT_VOLTAGE,
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_VOLTAGE,
    SENSOR_TYPE_ENERGY,
)
import logging

SCAN_INTERVAL = UPDATE_DELAY

_LOGGER = logging.getLogger(__name__)

temp_paneel = None
temp_lifetimeenergy = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an solarEdge entry."""
    # Add the needed sensors to hass
    client = hass.data[DOMAIN][entry.entry_id][DATA_API_CLIENT]

    site = await hass.async_add_executor_job(client.requestListOfAllPanels)

    _LOGGER.info("Found all information for site: %s", site.siteId)
    _LOGGER.info("Site has %s inverters", len(site.inverters))
    _LOGGER.info(
        "Adding all optimizers (%s) found to Home Assistant",
        site.returnNumberOfOptimizers(),
    )

    i = 1
    for inverter in site.inverters:
        _LOGGER.info("Adding all optimizers from inverter: %s", i)
        for string in inverter.strings:
            for optimizer in string.optimizers:
                _LOGGER.info(
                    "Added optimizer for panel_id: %s to Home Assistant",
                    optimizer.displayName,
                )

                # extra informatie ophalen
                info = await hass.async_add_executor_job(
                    client.requestSystemData, optimizer.optimizerId
                )
                if info is not None:
                    for sensortype in SENSOR_TYPE:
                        async_add_entities(
                            [
                                SolarEdgeOptimizersSensor(
                                    hass, client, entry, info, sensortype, optimizer
                                )
                            ],
                            update_before_add=False,
                        )

    _LOGGER.info(
        "Done adding all optimizers. Now adding sensors, this may take some time!"
    )


class SolarEdgeOptimizersSensor(SensorEntity):
    """bbbb"""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        hass: HomeAssistant,
        client: solaredgeoptimizers,
        entry: ConfigEntry,
        paneel: SolarEdgeOptimizerData,
        sensortype,
        optimizer: SolarlEdgeOptimizer,
    ) -> None:
        self._hass = hass
        self._client = client
        self._entry = entry
        self._paneelobject = paneel
        self._optimizerobject = optimizer
        self._paneel = paneel.paneel_desciption
        self._attr_unique_id = "{}_{}".format(paneel.serialnumber, sensortype)
        self._sensor_type = sensortype
        self._attr_name = "{}_{}".format(self._sensor_type, optimizer.displayName)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}")},
        )

        if self._sensor_type is SENSOR_TYPE_VOLTAGE:
            self._attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif self._sensor_type is SENSOR_TYPE_CURRENT:
            self._attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif self._sensor_type is SENSOR_TYPE_OPT_VOLTAGE:
            self._attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif self._sensor_type is SENSOR_TYPE_POWER:
            self._attr_native_unit_of_measurement = POWER_WATT
            self._attr_device_class = SensorDeviceClass.POWER
        elif self._sensor_type is SENSOR_TYPE_ENERGY:
            self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
            self._attr_device_class = SensorDeviceClass.ENERGY

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._paneelobject.serialnumber)
            },
            "name": self._optimizerobject.displayName,
            "manufacturer": self._paneelobject.manufacturer,
            "model": self._paneelobject.model,
            "hw_version": self._paneelobject.serialnumber,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    def update(self):
        """ddd"""
        global temp_paneel

        waarde = ""

        # Voor totaal energie moeten we wat anders doen
        if self._sensor_type is SENSOR_TYPE_ENERGY:
            # waarde ophalen
            response = ""

            try:
                response = self._client.getLifeTimeEnergy()

                if response != "":

                    if "ERROR001" in response:
                        _LOGGER.error(
                            "Error updating life time energy data for panel: %s",
                            self._paneelobject.paneel_id,
                        )
                        _LOGGER.error("The response was: %s", response)
                    else:
                        lifetimeenergy = json.loads(self._client.getLifeTimeEnergy())
                        waarde = round((
                            float(
                                lifetimeenergy[str(self._paneelobject.paneel_id)][
                                    "unscaledEnergy"
                                ]
                            )
                         / 1000 ),2)
            except Exception as err:
                _LOGGER.error(
                    "Error updating life time energy data for panel: %s",
                    self._paneelobject.paneel_id,
                )
                _LOGGER.error(err)
                _LOGGER.error("The response was: %s", response)
        else:

            try:

                if temp_paneel == None:
                    paneel_info = self._client.requestSystemData(
                        self._paneelobject.paneel_id
                    )
                    temp_paneel = paneel_info
                    _LOGGER.info(
                        "Paneel data opgehaald, geheugen was leeg. Paneel %s",
                        self._paneelobject.paneel_desciption,
                    )
                elif temp_paneel.paneel_id is not self._paneelobject.paneel_id:
                    paneel_info = self._client.requestSystemData(
                        self._paneelobject.paneel_id
                    )
                    temp_paneel = paneel_info
                    _LOGGER.info(
                        "Paneel data opgehaald, verkeerd paneel in geheugen. Paneel %s",
                        self._paneelobject.paneel_desciption,
                    )
                else:
                    paneel_info = temp_paneel
                    _LOGGER.info("Paneel data uit geheugen opgehaald")

            except Exception as err:
                _LOGGER.error(
                    "Error updating data for panel: %s", self._paneelobject.paneel_id
                )
                raise err

            # print(paneel_info)
            # {'Current [A]': '7.47', 'Optimizer Voltage [V]': '39.75', 'Power [W]': '253.00', 'Voltage [V]': '33.88'}

            waarde = ""

            if paneel_info is not None:
                if self._sensor_type is SENSOR_TYPE_VOLTAGE:
                    waarde = paneel_info.voltage
                elif self._sensor_type is SENSOR_TYPE_CURRENT:
                    waarde = paneel_info.current
                elif self._sensor_type is SENSOR_TYPE_OPT_VOLTAGE:
                    waarde = paneel_info.optimizer_voltage
                elif self._sensor_type is SENSOR_TYPE_POWER:
                    waarde = paneel_info.power
            else:
                return

        self._attr_native_value = waarde
