import asyncio
import aiohttp
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from aiohttp import ClientSession
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from .cync_server_utils import fetch_device_state, set_device_state
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CyncServerLightEntity(LightEntity):
    def __init__(self, device_ip, device_state, session):
        self._device_ip = device_ip
        self._device_state = device_state
        self._session = session

        self._attr_supported_color_modes = {
            ColorMode.HS,
            ColorMode.COLOR_TEMP
        }
        self._attr_min_color_temp_kelvin = 2000
        self._attr_max_color_temp_kelvin = 6500

    @property
    def unique_id(self):
        return f"{DOMAIN}_light_{self._device_ip}"

    @property
    def name(self):
        return self._device_state.get("name")

    @property
    def is_on(self):
        return bool(self._device_state.get("status"))

    @property
    def brightness(self):
        brightness = self._device_state.get("brightness")
        if brightness is not None:
            return int(brightness * 255 / 100)
        return None

    @property
    def color_temp_kelvin(self):
        try:
            percent = int(self._device_state.get("temperature"))
            kelvin = int(2000 + ((100 - percent) / 100) * (6500 - 2000))
            return kelvin
        except Exception as e:
            _LOGGER.debug("Failed to get kelvin temperature: %s", e)
            return None


    @property
    def hs_color(self):
        color = self._device_state.get("color")
        if color:
            # Convert RGB to HS (hue/sat) if your device stores RGB
            from colorsys import rgb_to_hsv

            r, g, b = color.get("r", 0), color.get("g", 0), color.get("b", 0)
            r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
            h, s, _ = rgb_to_hsv(r_f, g_f, b_f)
            return (h * 360, s * 100)
        return None

    async def async_set_hs_color(self, hs_color):
        from colorsys import hsv_to_rgb

        h, s = hs_color
        r, g, b = hsv_to_rgb(h / 360.0, s / 100.0, 1.0)
        color = {"r": int(r * 255), "g": int(g * 255), "b": int(b * 255)}
        data = {"color": color, "id": str(self._device_state.get("id"))}
        _LOGGER.debug("Setting HS color on %s with payload: %s", self._device_ip, data)
        success = await set_device_state(self._session, self._device_ip, data)
        if success:
            self._device_state["color"] = color
            self.async_write_ha_state()
        else:
            _LOGGER.debug("Data async color set not succesful")

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("Turn On kwargs: %s", str(kwargs))
        if ATTR_BRIGHTNESS in kwargs:
            await self.async_set_brightness(kwargs[ATTR_BRIGHTNESS])
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            await self.async_set_color_temp_kelvin(kwargs[ATTR_COLOR_TEMP_KELVIN])
        # elif ATTR_RGB_COLOR in kwargs:
        #     await self.async_set_rgb_color(kwargs[ATTR_RGB_COLOR])
        elif ATTR_HS_COLOR in kwargs:
            await self.async_set_hs_color(kwargs[ATTR_HS_COLOR])
        else:
            data = {"status": "1", "id": str(str(self._device_state.get("id")))}
            success = await set_device_state(self._session, self._device_ip, data)
            _LOGGER.debug("Data async Turn On: %s", data)
            _LOGGER.debug("Device State: %s", self._device_state)
            if success:
                self._device_state["status"] = True
                self.async_write_ha_state()
                self.async_schedule_update_ha_state(force_refresh=True)
            else:
                _LOGGER.debug("Data async Turn On not succesful")

    async def async_turn_off(self, **kwargs):
        data = {"status": "0", "id": str(self._device_state.get("id"))}
        success = await set_device_state(self._session, self._device_ip, data)
        _LOGGER.debug("Data async Turn Off: %s", data)
        if success:
            self._device_state["status"] = False
            self.async_write_ha_state()
            self.async_schedule_update_ha_state(force_refresh=True)
        else:
            _LOGGER.debug("Data async Turn Off not succesful")

    async def async_set_brightness(self, brightness):
        scaled_brightness = int(brightness * 100 / 255)
        data = {
            "brightness": scaled_brightness,
            "id": str(self._device_state.get("id")),
        }
        success = await set_device_state(self._session, self._device_ip, data)
        _LOGGER.debug("Data async Brightness: %s", data)
        if success:
            self._device_state["brightness"] = scaled_brightness
            self.async_write_ha_state()
            self.async_schedule_update_ha_state(force_refresh=True)
        else:
            _LOGGER.debug("Data async Brightness not succesful")

    async def async_set_color_temp_kelvin(self, kelvin):
        # Convert from Kelvin back to 0–100 reversed scale
        if kelvin < 2000:
            kelvin = 2000
        elif kelvin > 6500:
            kelvin = 6500

        percent = (kelvin - 2000) / (6500 - 2000) * 100
        reversed_temperature = int(100 - percent)

        data = {
            "temperature": str(reversed_temperature),
            "id": str(self._device_state.get("id")),
        }

        success = await set_device_state(self._session, self._device_ip, data)
        _LOGGER.debug("Data async Temp (Kelvin): %s", data)

        if success:
            self._device_state["temperature"] = reversed_temperature
            self.async_write_ha_state()
            self.async_schedule_update_ha_state(force_refresh=True)


    async def async_update(self):
        device_state = await fetch_device_state(self._session, self._device_ip)
        _LOGGER.debug("Data async Update: %s", device_state)
        if device_state:
            self._device_state = device_state

            if "color" in device_state and device_state["color"]:
                self._attr_color_mode = ColorMode.HS
            elif "temperature" in device_state:
                self._attr_color_mode = ColorMode.COLOR_TEMP


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    server_ip = entry.data["server_ip"]
    device_ips = hass.data[DOMAIN][entry.entry_id]["device_ips"]
    session = hass.data[DOMAIN][entry.entry_id]["session"]

    lights = []
    for device_ip in device_ips:
        device_state = await fetch_device_state(session, device_ip)
        if device_state:
            lights.append(CyncServerLightEntity(device_ip, device_state, session))

    async_add_entities(lights, update_before_add=True)
    return True
