"""The SolarEdge Optimizers Data integration."""
from requests import ConnectTimeout, HTTPError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .solaredgeoptimizers import solaredgeoptimizers
from .const import CONF_SITE_ID, DOMAIN, LOGGER, DATA_API_CLIENT, PANEEL_DATA

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdge Optimizers Data from a config entry."""

    # ELKE KEER RUNT DIT TIJDENS HET OPSTARTEN
    # print("kom je hier bij het begin? Of elke keer?")
    print("__init__.py -> async_setup_entry")
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

    # Hiet moeten we deels wat faken, want ik heb niet alles beschikbaar nog!
    # De panelen lijst bv wel, belangrijk!

    # panelen = await hass.async_add_executor_job(api.requestListOfAllPanels)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_API_CLIENT: api}

    # print(panelen)
    # for paneel in panelen:
    #     print(paneel)
    #     print("setup platforms for paneel: {}".format(paneel.split("|")[0]))
    #     # print(hass.data)

    #     hass.data[DOMAIN][PANEEL_DATA] = {PANEEL_DATA: paneel}
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
