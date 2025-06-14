import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "cync_server"


class CyncServerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Perform validation and configuration setup
            # ...

            return self.async_create_entry(title="Cync Server", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("server_ip"): str}),
        )


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    return True
