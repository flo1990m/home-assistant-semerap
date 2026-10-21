"""Water meter index, historical statistics and archived statement data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from homeassistant.components.sensor import (
    SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PDC, DOMAIN


@dataclass(frozen=True, kw_only=True)
class SemerapSensorDescription(SensorEntityDescription):
    field: str


SENSORS = (
    SemerapSensorDescription(key="index", name="Index compteur", field="index",
                             native_unit_of_measurement="m³",
                             device_class=SensorDeviceClass.WATER,
                             state_class=SensorStateClass.TOTAL_INCREASING),
    SemerapSensorDescription(key="consumption", name="Consommation dernier relevé", field="consumption",
                             native_unit_of_measurement="m³"),
    SemerapSensorDescription(key="daily", name="Moyenne quotidienne dernière période", field="dailyCons",
                             native_unit_of_measurement="m³/d"),
    SemerapSensorDescription(key="date", name="Date dernier relevé", field="date",
                             device_class=SensorDeviceClass.DATE),
    SemerapSensorDescription(key="avg", name="Moyenne historique du fournisseur", field="avgCons",
                             native_unit_of_measurement="m³"),
    SemerapSensorDescription(key="date_fr", name="Date dernier relevé (français)", field="date_fr"),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SemerapSensor(coordinator, entry, description) for description in SENSORS)


class SemerapSensor(CoordinatorEntity, SensorEntity):
    entity_description: SemerapSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        pdc = str(entry.data[CONF_PDC])
        self._attr_unique_id = f"{pdc}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pdc)},
            name="Compteur eau SEMERAP",
            manufacturer="SEMERAP",
        )

    @property
    def native_value(self):
        row = self.coordinator.data["latest"]
        key = self.entity_description.key
        value = row.get(self.entity_description.field)
        if key == "date":
            try:
                return date.fromisoformat(value)
            except (TypeError, ValueError):
                return None
        if key == "date_fr":
            try:
                return date.fromisoformat(row["date"]).strftime("%d/%m/%Y")
            except (KeyError, TypeError, ValueError):
                return None
        return value if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "index":
            return None
        history = self.coordinator.data["history"]
        latest = history[0]
        return {
            "last_reading_date": latest["date"],
            "last_reading_date_fr": date.fromisoformat(latest["date"]).strftime("%d/%m/%Y"),
            "readings_count": len(history),
            "reading_type": latest.get("type"),
            "readings": [
                {"date": r["date"],
                 "date_fr": date.fromisoformat(r["date"]).strftime("%d/%m/%Y"),
                 "index": r["index"],
                 "consumption": r.get("consumption"),
                 "daily_consumption": r.get("dailyCons")}
                for r in reversed(history)
            ],
        }
