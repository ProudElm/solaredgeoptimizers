"""Platform for sensor integration."""
from homeassistant.helpers.entity import DeviceInfo

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
)

from .solaredgeoptimizers import SolarEdgeOptimizerData, solaredgeoptimizers
from .const import (
    DATA_API_CLIENT,
    DOMAIN,
    UPDATE_DELAY,
    SENSOR_TYPE,
    SENSOR_TYPE_OPT_VOLTAGE,
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_VOLTAGE,
)

SCAN_INTERVAL = UPDATE_DELAY


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an solarEdge entry."""
    # Add the needed sensors to hass
    client = hass.data[DOMAIN][entry.entry_id][DATA_API_CLIENT]

    panelen = await hass.async_add_executor_job(client.requestAllData)

    for paneel in panelen:
        for sensortype in SENSOR_TYPE:
            async_add_entities(
                [SolarEdgeOptimizersSensor(client, entry, paneel, sensortype)],
                update_before_add=True,
            )


class SolarEdgeOptimizersSensor(SensorEntity):
    """bbbb"""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        client: solaredgeoptimizers,
        entry: ConfigEntry,
        paneel: SolarEdgeOptimizerData,
        sensortype,
    ) -> None:
        self._client = client
        self._entry = entry
        self._paneelobject = paneel
        self._paneel = paneel.paneel_desciption
        self._attr_unique_id = "{}_{}".format(paneel.serialnumber, sensortype)
        self._sensor_type = sensortype
        self._attr_name = self._sensor_type

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

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._paneelobject.serialnumber)
            },
            "name": "Paneel: {}".format(self._paneel),
            "manufacturer": self._paneelobject.manufacturer,
            "model": self._paneelobject.model,
            "hw_version": self._paneelobject.serialnumber,
            "via_device": (DOMAIN, self._entry.entry_id),
        }

    def update(self):
        """ddd"""
        paneel_info = ""

        try:
            paneel_info = self._client.requestSystemData(self._paneelobject.paneel_id)
        except Exception as err:
            print(err)
            raise err

        # print(paneel_info)
        # {'Current [A]': '7.47', 'Optimizer Voltage [V]': '39.75', 'Power [W]': '253.00', 'Voltage [V]': '33.88'}
        waarde = ""

        if self._sensor_type is SENSOR_TYPE_VOLTAGE:
            waarde = paneel_info.voltage
        elif self._sensor_type is SENSOR_TYPE_CURRENT:
            waarde = paneel_info.current
        elif self._sensor_type is SENSOR_TYPE_OPT_VOLTAGE:
            waarde = paneel_info.optimizer_voltage
        elif self._sensor_type is SENSOR_TYPE_POWER:
            waarde = paneel_info.power

        print(
            "Update paneel: {}. Sensor type: {}. Waarde {} {}".format(
                paneel_info.paneel_desciption,
                self._sensor_type,
                waarde,
                self._attr_native_unit_of_measurement,
            )
        )

        self._attr_native_value = waarde
