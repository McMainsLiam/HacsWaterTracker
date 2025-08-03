"""DataUpdateCoordinator for Plano Water."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PlanoWaterAPI
from .const import CONF_PASSWORD, CONF_USERNAME, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlanoWaterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Plano Water portal."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api = PlanoWaterAPI(
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Ensure we're logged in
            if not await self.api.async_login():
                raise UpdateFailed("Failed to login to Plano Water portal")

            # Get account info if not already cached
            if not self.api.account_info:
                account_info = await self.api.async_get_account_info()
                if not account_info:
                    raise UpdateFailed("Failed to get account information")

            # Get usage data from AccountSummary page
            usage_data = await self.api.async_get_usage_data()
            if not usage_data:
                raise UpdateFailed("Failed to get usage data from AccountSummary page")

            return {
                "account_info": self.api.account_info,
                "usage_data": usage_data,
            }

        except Exception as exc:
            raise UpdateFailed(f"Error communicating with Plano Water portal: {exc}") from exc

    async def async_shutdown(self) -> None:
        """Close API session."""
        await self.api.async_close()