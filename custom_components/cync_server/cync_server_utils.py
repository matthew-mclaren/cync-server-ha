import asyncio
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


async def fetch_device_state(session: aiohttp.ClientSession, device_ip: str) -> dict:
    # Update the URL to match your server's API endpoint
    url = f"http://192.168.1.1:8080/api/devices/{device_ip}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                _LOGGER.debug(
                    "Error fetching device state for %s. Status: %s",
                    device_ip,
                    response.status,
                )
    except aiohttp.ClientError as err:
        _LOGGER.debug("Error fetching device state for %s: %s", device_ip, err)
    return None


async def set_device_state(
    session: aiohttp.ClientSession, device_ip: str, data: dict
) -> bool:
    # Update the URL to match your server's API endpoint
    url = f"http://192.168.1.1:8080/api/devices/{device_ip}"
    try:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                return True
            else:
                _LOGGER.debug(
                    "Error setting device state for %s. Status: %s",
                    device_ip,
                    response.status,
                )
    except aiohttp.ClientError as err:
        _LOGGER.debug("Error setting device state for %s: %s", device_ip, err)
    return False
