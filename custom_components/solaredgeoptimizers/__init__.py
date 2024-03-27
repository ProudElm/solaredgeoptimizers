"""The SolarEdge Optimizers Data integration."""

from requests import ConnectTimeout, HTTPError
from solaredgeoptimizers import SolarEdgeSite, solaredgeoptimizers

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DATA_API_CLIENT, DATA_COORDINATOR, DATA_SITE, DOMAIN, LOGGER
from .coordinator import SolarEdgeOptimizersCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdge Optimizers Data from a config entry."""

    api = solaredgeoptimizers(
        entry.data["siteid"], entry.data["username"], entry.data["password"]
    )

    def _get_site() -> SolarEdgeSite | None:
        code = api.check_login()
        return api.requestListOfAllPanels() if code == 200 else None

    try:
        site = await hass.async_add_executor_job(_get_site)
    except (ConnectTimeout, HTTPError) as ex:
        LOGGER.error("Could not retrieve details from SolarEdge API")
        raise ConfigEntryNotReady from ex

    if not site:
        LOGGER.error("Missing details data in SolarEdge response")
        raise ConfigEntryNotReady

    coordinator = SolarEdgeOptimizersCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_API_CLIENT: api,
        DATA_SITE: site,
        DATA_COORDINATOR: coordinator,
    }

    dr = async_get_device_registry(hass)
    dr.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["siteid"]), (DOMAIN, entry.entry_id)},
        manufacturer="SolarEdge",
        name=f"Site {entry.data['siteid']}",
        model="SolarEdge Optimizers",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
