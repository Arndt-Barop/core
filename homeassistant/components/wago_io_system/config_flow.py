"""Config flow for WAGO I/O System integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class WAGOIOSystemConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WAGO I/O System."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        # Connection test and validation will be implemented in next commits
        # Unique ID will be set based on device info
        # Duplicate entry checking will be added

        return self.async_create_entry(
            title=f"WAGO Controller ({user_input[CONF_HOST]})",
            data=user_input,
        )
