"""Example integration using DataUpdateCoordinator."""

import asyncio
from datetime import datetime
import logging

from solaredgeoptimizers import SolarEdgeOptimizerData, solaredgeoptimizers

# from homeassistant.const import (
#     POWER_WATT,
#     ELECTRIC_POTENTIAL_VOLT,
#     ELECTRIC_CURRENT_AMPERE,
#     ENERGY_KILO_WATT_HOUR,
# )
# FROM 2023.2!
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CHECK_TIME_DELTA, UPDATE_DELAY

_LOGGER = logging.getLogger(__name__)


class SolarEdgeOptimizersCoordinator(
    DataUpdateCoordinator[dict[int, SolarEdgeOptimizerData] | None]
):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api: solaredgeoptimizers) -> None:
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
        self.first_boot = True

    async def _async_update_data(self) -> dict[int, SolarEdgeOptimizerData] | None:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(300):
                _LOGGER.debug("Update from the coordinator")
                data: list[
                    SolarEdgeOptimizerData
                ] = await self.hass.async_add_executor_job(self.my_api.requestAllData)

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
                    return {optimizer.paneel_id: optimizer for optimizer in data}
                _LOGGER.debug("No new data to enter")
                return None

        except Exception as err:
            _LOGGER.error("Error in updating updater")
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
