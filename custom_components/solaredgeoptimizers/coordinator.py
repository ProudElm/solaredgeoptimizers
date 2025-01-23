"""Example integration using DataUpdateCoordinator."""
from datetime import datetime

import logging
import async_timeout

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    UPDATE_DELAY,
    CHECK_TIME_DELTA,
)

from solaredgeoptimizers import (
    solaredgeoptimizers,
)

_LOGGER = logging.getLogger(__name__)

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