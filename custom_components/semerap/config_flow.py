"""UI configuration for SEMERAP."""
from __future__ import annotations

from collections.abc import Mapping

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SemerapAuthError, SemerapClient, SemerapError
from .const import CONF_PDC, DOMAIN


class SemerapConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup flow."""
        errors = {}
        if user_input is not None:
            client = SemerapClient(
                async_get_clientsession(self.hass),
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                pdcs = await client.pdcs()
                if not pdcs:
                    raise SemerapError("No metering point found")
            except SemerapAuthError:
                errors["base"] = "invalid_auth"
            except SemerapError:
                errors["base"] = "cannot_connect"
            else:
                pdc = str(pdcs[0]["pdcRef"])
                await self.async_set_unique_id(f"{user_input[CONF_USERNAME]}_{pdc}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SEMERAP {pdc}",
                    data={**user_input, CONF_PDC: pdc},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, object]
    ) -> config_entries.ConfigFlowResult:
        """Start the reauthentication flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for new credentials and validate them."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            client = SemerapClient(
                async_get_clientsession(self.hass),
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                # Validate the credentials and ensure the account still exposes
                # the meter linked to this config entry.
                pdcs = await client.pdcs()
                if not any(str(pdc["pdcRef"]) == str(entry.data[CONF_PDC]) for pdc in pdcs):
                    raise SemerapError("Configured metering point was not found")
            except SemerapAuthError:
                errors["base"] = "invalid_auth"
            except SemerapError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=entry.data[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
