"""The SolarEdge Optimizers Data integration."""
from requests import ConnectTimeout, HTTPError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady


from solaredgeoptimizers import solaredgeoptimizers
from .const import (
    CONF_SITE_ID,
    DOMAIN,
    LOGGER,
    DATA_API_CLIENT,
    PANEEL_DATA,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdge Optimizers Data from a config entry."""

    api = solaredgeoptimizers(
        entry.data["siteid"], entry.data["username"], entry.data["password"]
    )
    try:
        http_result_code = await hass.async_add_executor_job(api.check_login)
    except (ConnectTimeout, HTTPError) as ex:
        LOGGER.error("Could not retrieve details from SolarEdge API")
        raise ConfigEntryNotReady from ex

    if http_result_code != 200:
        LOGGER.error("Missing details data in SolarEdge response")
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_API_CLIENT: api}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
