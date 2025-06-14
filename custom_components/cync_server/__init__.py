import asyncio
import aiohttp
import logging

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .light import CyncServerLightEntity
from .cync_server_utils import fetch_device_state, set_device_state

_LOGGER = logging.getLogger(__name__)

DOMAIN = "cync_server"


async def fetch_device_ips(session: aiohttp.ClientSession) -> list[str]:
    try:
        # Update the URL to match your server's API endpoint
        async with session.get("http://192.168.1.1:8080/api/devices") as response:
            devices = await response.json()
            return [device for device in devices]
    except aiohttp.ClientError as ex:
        _LOGGER.error("Failed to fetch device IPs: %s", ex)
        return []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server_ip = entry.data["server_ip"]
    session = aiohttp.ClientSession()

    device_ips = await fetch_device_ips(session)

    hass.data[DOMAIN][entry.entry_id] = {
        "server_ip": server_ip,
        "device_ips": device_ips,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["light"])
    return True
