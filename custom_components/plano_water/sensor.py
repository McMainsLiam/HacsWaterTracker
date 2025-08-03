"""Sensor platform for Plano Water integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import PlanoWaterDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(PlanoWaterSensor(coordinator, sensor_type))

    async_add_entities(entities, False)


class PlanoWaterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Plano Water sensor."""

    def __init__(
        self,
        coordinator: PlanoWaterDataUpdateCoordinator,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self.sensor_config = SENSOR_TYPES[sensor_type]
        
        account_number = ""
        if coordinator.data and "account_info" in coordinator.data:
            account_number = coordinator.data["account_info"].get("account_number", "")
        
        self._attr_name = f"Plano Water {self.sensor_config['name']}"
        self._attr_unique_id = f"plano_water_{account_number}_{sensor_type}"
        self._attr_native_unit_of_measurement = self.sensor_config["unit"]
        self._attr_icon = self.sensor_config["icon"]
        
        if self.sensor_config["device_class"]:
            if self.sensor_config["device_class"] == "timestamp":
                self._attr_device_class = SensorDeviceClass.TIMESTAMP
            else:
                self._attr_device_class = getattr(SensorDeviceClass, self.sensor_config["device_class"].upper())
            
        if self.sensor_config["state_class"]:
            self._attr_state_class = getattr(SensorStateClass, self.sensor_config["state_class"].upper())

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        account_info = {}
        if self.coordinator.data and "account_info" in self.coordinator.data:
            account_info = self.coordinator.data["account_info"]
            
        return {
            "identifiers": {(DOMAIN, account_info.get("account_number", "unknown"))},
            "name": f"Plano Water Account {account_info.get('account_number', 'Unknown')}",
            "manufacturer": "City of Plano",
            "model": "Water Meter",
            "sw_version": account_info.get("meter_number", "Unknown"),
        }

    @property
    def native_value(self) -> str | float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        usage_data = self.coordinator.data.get("usage_data", {})
        
        if self.sensor_type == "current_usage":
            return usage_data.get("current_usage", 0)
        elif self.sensor_type == "daily_usage":
            return usage_data.get("daily_usage", 0)
        elif self.sensor_type == "last_reading":
            last_reading = usage_data.get("last_reading")
            if last_reading:
                try:
                    # Parse the datetime string from the format: "11/26/24 3:00 AM"
                    date_obj = datetime.strptime(last_reading, "%m/%d/%y %I:%M %p")
                    # Return as datetime object for timestamp device class
                    return date_obj
                except ValueError:
                    _LOGGER.warning("Could not parse datetime: %s", last_reading)
                    return None
            return None

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        account_info = self.coordinator.data.get("account_info", {})
        usage_data = self.coordinator.data.get("usage_data", {})
        
        attributes = {
            "account_number": account_info.get("account_number"),
            "meter_number": account_info.get("meter_number"),
            "account_name": account_info.get("name"),
            "last_updated": datetime.now().isoformat(),
        }

        # Add sensor-specific attributes
        if self.sensor_type == "current_usage":
            attributes["last_reading_date"] = usage_data.get("last_reading")
        elif self.sensor_type == "daily_usage":
            attributes["reading_count"] = len(usage_data.get("raw_data", []))
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None