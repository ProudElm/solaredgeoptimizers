"""Example integration using DataUpdateCoordinator."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from datetime import datetime, timedelta

import logging

import async_timeout
import pytz

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.core import callback

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
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
    SENSOR_TYPE_LASTMEASUREMENT,
    CHECK_TIME_DELTA,
)


# from homeassistant.const import (
#     POWER_WATT,
#     ELECTRIC_POTENTIAL_VOLT,
#     ELECTRIC_CURRENT_AMPERE,
#     ENERGY_KILO_WATT_HOUR,
# )

# FROM 2023.2!
from homeassistant.const import (
    UnitOfPower,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfEnergy,
)

from solaredgeoptimizers import (
    SolarEdgeOptimizerData,
    solaredgeoptimizers,
    SolarlEdgeOptimizer,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an solarEdge entry."""
    # Add the needed sensors to hass
    my_api = hass.data[DOMAIN][entry.entry_id][DATA_API_CLIENT]
    site = await hass.async_add_executor_job(my_api.requestListOfAllPanels)

    coordinator = MyCoordinator(hass, my_api, True)

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
                    my_api.requestSystemData, optimizer.optimizerId
                )

                if info is not None:
                    for sensortype in SENSOR_TYPE:
                        async_add_entities(
                            [
                                SolarEdgeOptimizersSensor(
                                    coordinator,
                                    hass,
                                    entry,
                                    info,
                                    sensortype,
                                    optimizer,
                                )
                            ],
                            update_before_add=True,
                        )

    _LOGGER.info(
        "Done adding all optimizers. Now adding sensors, this may take some time!"
    )


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, my_api: solaredgeoptimizers, first_boot):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="SolarEdgeOptimizer",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=UPDATE_DELAY,
        )
        self.my_api = my_api
        self.first_boot = first_boot

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(300):
                _LOGGER.debug("Update from the coordinator")
                data = await self.hass.async_add_executor_job(
                    self.my_api.requestAllData
                )

                update = False

                timetocheck = datetime.now() - CHECK_TIME_DELTA

                for optimizer in data:
                    _LOGGER.debug(
                        "Checking time: %s | Versus last measerument: %s",
                        timetocheck,
                        optimizer.lastmeasurement,
                    )

                    if optimizer.lastmeasurement > timetocheck:
                        update = True
                        break

                if update or self.first_boot:
                    _LOGGER.debug("We enter new data")
                    self.first_boot = False
                    return data
                else:
                    _LOGGER.debug("No new data to enter")
                    return None

        except Exception as err:
            _LOGGER.error("Error in updating updater")
            _LOGGER.error(err)
            raise UpdateFailed(err)


# class MyEntity(CoordinatorEntity, SensorEntity):
class SolarEdgeOptimizersSensor(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator,
        hass: HomeAssistant,
        entry: ConfigEntry,
        paneel: SolarEdgeOptimizerData,
        sensortype,
        optimizer: SolarlEdgeOptimizer,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
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
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif self._sensor_type is SENSOR_TYPE_CURRENT:
            self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
            self._attr_device_class = SensorDeviceClass.CURRENT
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif self._sensor_type is SENSOR_TYPE_OPT_VOLTAGE:
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif self._sensor_type is SENSOR_TYPE_POWER:
            self._attr_native_unit_of_measurement = UnitOfPower.WATT
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif self._sensor_type is SENSOR_TYPE_ENERGY:
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif self._sensor_type is SENSOR_TYPE_LASTMEASUREMENT:
            self._attr_device_class = SensorDeviceClass.DATE
            self._attr_state_class = None

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self.coordinator.data is not None:

            _LOGGER.debug(
                "Update the sensor %s - %s with the info from the coordinator",
                self._paneelobject.paneel_id,
                self._sensor_type,
            )

            for item in self.coordinator.data:
                if item.paneel_id == self._paneelobject.paneel_id:
                    # weird first time after reboot value is None
                    # if self._attr_native_value is not None:
                    if self._sensor_type is SENSOR_TYPE_VOLTAGE:
                        self._attr_native_value = item.voltage
                        break
                    elif self._sensor_type is SENSOR_TYPE_CURRENT:
                        self._attr_native_value = item.current
                        break
                    elif self._sensor_type is SENSOR_TYPE_OPT_VOLTAGE:
                        self._attr_native_value = item.optimizer_voltage
                        break
                    elif self._sensor_type is SENSOR_TYPE_POWER:
                        self._attr_native_value = item.power
                        break
                    elif self._sensor_type is SENSOR_TYPE_ENERGY:
                        if (
                            self._attr_native_value is None
                            or item.lifetime_energy >= self._attr_native_value
                        ):
                            self._attr_native_value = item.lifetime_energy
                            break
                        else:
                            self._attr_native_value = self._attr_native_value
                    elif self._sensor_type is SENSOR_TYPE_LASTMEASUREMENT:
                        self._attr_native_value = item.lastmeasurement
                        break
        else:
            # Set the value to zero. (BUT NOT FOR LIFETIME ENERGY)
            if (not self._sensor_type is SENSOR_TYPE_ENERGY) and (
                not self._sensor_type is SENSOR_TYPE_LASTMEASUREMENT
            ):
                self._attr_native_value = 0

        self.async_write_ha_state()
