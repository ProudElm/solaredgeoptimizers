"""Example integration using DataUpdateCoordinator."""

import logging

from solaredgeoptimizers import (
    SolarEdgeOptimizerData,
    SolarEdgeSite,
    SolarlEdgeOptimizer,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry

# from homeassistant.const import (
#     POWER_WATT,
#     ELECTRIC_POTENTIAL_VOLT,
#     ELECTRIC_CURRENT_AMPERE,
#     ENERGY_KILO_WATT_HOUR,
# )
# FROM 2023.2!
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DATA_SITE,
    DOMAIN,
    SENSOR_TYPE,
    SENSOR_TYPE_CURRENT,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_LASTMEASUREMENT,
    SENSOR_TYPE_OPT_VOLTAGE,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_VOLTAGE,
)
from .coordinator import SolarEdgeOptimizersCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add an solarEdge entry."""
    # Add the needed sensors to hass
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SolarEdgeOptimizersCoordinator = entry_data[DATA_COORDINATOR]
    site: SolarEdgeSite = entry_data[DATA_SITE]

    _LOGGER.info("Found all information for site: %s", site.siteId)
    _LOGGER.info("Site has %s inverters", len(site.inverters))
    _LOGGER.info(
        "Adding all optimizers (%s) found to Home Assistant",
        site.returnNumberOfOptimizers(),
    )

    i = 1
    entities: list[SolarEdgeOptimizersSensor] = []
    optimizer_data: dict[int, SolarEdgeOptimizerData] | None = coordinator.data
    assert optimizer_data is not None
    for inverter in site.inverters:
        _LOGGER.info("Adding all optimizers from inverter: %s", i)
        for string in inverter.strings:
            for optimizer in string.optimizers:
                _LOGGER.info(
                    "Added optimizer for panel_id: %s (%s) to Home Assistant",
                    optimizer.displayName,
                    optimizer.optimizerId,
                )

                # extra informatie ophalen
                if info := optimizer_data.get(optimizer.optimizerId):
                    entities.extend(
                        SolarEdgeOptimizersSensor(
                            coordinator,
                            entry,
                            info,
                            sensortype,
                            optimizer,
                        )
                        for sensortype in SENSOR_TYPE
                    )

    _LOGGER.info(
        "Done adding all optimizers. Now adding sensors, this may take some time!"
    )
    async_add_entities(entities)


# class MyEntity(CoordinatorEntity, SensorEntity):
class SolarEdgeOptimizersSensor(
    CoordinatorEntity[SolarEdgeOptimizersCoordinator], SensorEntity
):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(
        self,
        coordinator: SolarEdgeOptimizersCoordinator,
        entry: ConfigEntry,
        paneel: SolarEdgeOptimizerData,
        sensortype: str,
        optimizer: SolarlEdgeOptimizer,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._paneelobject = paneel
        self._optimizerobject = optimizer
        self._paneel = paneel.paneel_desciption
        self._attr_unique_id = f"{paneel.serialnumber}_{sensortype}"
        self._sensor_type = sensortype
        self._attr_name = f"{self._sensor_type}_{optimizer.displayName}"

        if sensortype == SENSOR_TYPE_VOLTAGE:
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensortype == SENSOR_TYPE_CURRENT:
            self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
            self._attr_device_class = SensorDeviceClass.CURRENT
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensortype == SENSOR_TYPE_OPT_VOLTAGE:
            self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensortype == SENSOR_TYPE_POWER:
            self._attr_native_unit_of_measurement = UnitOfPower.WATT
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensortype == SENSOR_TYPE_ENERGY:
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif sensortype == SENSOR_TYPE_LASTMEASUREMENT:
            self._attr_device_class = SensorDeviceClass.DATE

        self._attr_device_info = {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, paneel.serialnumber),
            },
            "name": optimizer.displayName,
            "manufacturer": paneel.manufacturer,
            "model": paneel.model,
            "hw_version": paneel.serialnumber,
            "via_device": (DOMAIN, entry.entry_id),
        }
        self._update_from_latest_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_latest_data()
        super()._handle_coordinator_update()

    def _update_from_latest_data(self) -> None:
        """Handle updated data from the coordinator."""
        data: dict[int, SolarEdgeOptimizerData] | None
        sensor_type = self._sensor_type

        if (data := self.coordinator.data) is not None:
            _LOGGER.info(
                "Update the sensor %s - %s with the info from the coordinator",
                self._paneelobject.paneel_id,
                sensor_type,
            )
            if item := data.get(self._paneelobject.paneel_id):
                _LOGGER.warning("Item: %s %s", item, dir(item))
                # weird first time after reboot value is None
                # if self._attr_native_value is not None:
                if sensor_type == SENSOR_TYPE_VOLTAGE:
                    self._attr_native_value = item.voltage
                elif sensor_type == SENSOR_TYPE_CURRENT:
                    self._attr_native_value = item.current
                elif sensor_type == SENSOR_TYPE_OPT_VOLTAGE:
                    self._attr_native_value = item.optimizer_voltage
                elif sensor_type == SENSOR_TYPE_POWER:
                    self._attr_native_value = item.power
                elif sensor_type == SENSOR_TYPE_ENERGY:
                    if (
                        self._attr_native_value is None
                        or item.lifetime_energy >= self._attr_native_value
                    ):
                        self._attr_native_value = item.lifetime_energy
                    else:
                        self._attr_native_value = self._attr_native_value
                elif sensor_type == SENSOR_TYPE_LASTMEASUREMENT:
                    self._attr_native_value = item.lastmeasurement

        elif sensor_type not in (SENSOR_TYPE_ENERGY, SENSOR_TYPE_LASTMEASUREMENT):
            self._attr_native_value = 0
