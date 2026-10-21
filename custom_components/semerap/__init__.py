"""SEMERAP water consumption integration with persistent reading archive."""
from __future__ import annotations

import logging

import voluptuous as vol
from datetime import date, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SemerapAuthError, SemerapClient, SemerapError
from .const import CONF_PDC, DOMAIN

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
SERVICE_IMPORT = "import_readings"
IMPORT_SCHEMA = vol.Schema({
    vol.Optional(CONF_PDC): str,
    vol.Required("readings"): vol.All([dict], vol.Length(min=1)),
})


def _normalize_reading(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    try:
        reading_date = date.fromisoformat(str(item["date"]))
        index = item["index"]
        if isinstance(index, bool) or not isinstance(index, (int, float)) or index < 0:
            return None
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    record = {"date": reading_date.isoformat(), "index": index}
    for key in ("consumption", "dailyCons", "avgCons"):
        value = item.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            record[key] = value
    for key in ("type", "counterRef"):
        value = item.get(key)
        if isinstance(value, str):
            record[key] = value
    return record


class SemerapCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: SemerapClient, pdc: str):
        super().__init__(hass, _LOGGER, name=f"SEMERAP {pdc}",
                         update_interval=timedelta(days=1))
        self.client = client
        self.pdc = pdc
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{pdc}.readings")
        self._archive: dict[str, dict[str, Any]] = {}

    async def async_load_archive(self) -> None:
        stored = await self._store.async_load()
        rows = stored.get("readings", []) if isinstance(stored, dict) else []
        for row in rows if isinstance(rows, list) else []:
            record = _normalize_reading(row)
            if record:
                self._archive[record["date"]] = record

    async def async_import_readings(self, rows: list[dict[str, Any]]) -> int:
        """Validate and persist historical readings without overwriting API data."""
        incoming: dict[str, dict[str, Any]] = {}
        for position, row in enumerate(rows, start=1):
            normalized = _normalize_reading(row)
            if normalized is None:
                raise HomeAssistantError(
                    f"Invalid reading #{position}: expected ISO date YYYY-MM-DD, "
                    "nonnegative numeric index and optional numeric consumption"
                )
            if row.get("consumption") is not None and "consumption" not in normalized:
                raise HomeAssistantError(f"Invalid consumption in reading #{position}")
            if normalized["date"] in incoming:
                raise HomeAssistantError(f"Duplicate date within import: {normalized['date']}")
            incoming[normalized["date"]] = normalized

        added = {d: v for d, v in incoming.items() if d not in self._archive}
        if not added:
            return 0
        updated = {**self._archive, **added}
        try:
            await self._store.async_save({
                "pdc_ref": self.pdc,
                "readings": sorted(updated.values(), key=lambda r: r["date"]),
            })
        except Exception as err:
            raise HomeAssistantError("Could not save SEMERAP historical readings") from err
        self._archive = updated
        self.async_set_updated_data(self._result())
        return len(added)

    def _result(self) -> dict[str, Any]:
        history = sorted(self._archive.values(), key=lambda row: row["date"], reverse=True)
        return {"latest": history[0], "history": history}

    async def _async_update_data(self):
        try:
            rows = await self.client.statements(self.pdc)
        except SemerapAuthError as err:
            raise ConfigEntryAuthFailed("SEMERAP authentication failed") from err
        except SemerapError as err:
            raise UpdateFailed(str(err)) from err
        if not isinstance(rows, list):
            raise UpdateFailed("Invalid SEMERAP readings")
        incoming = {}
        for row in rows:
            normalized = _normalize_reading(row)
            if normalized:
                incoming[normalized["date"]] = normalized
        if incoming:
            updated = dict(self._archive)
            updated.update(incoming)
            if updated != self._archive:
                try:
                    await self._store.async_save({
                        "pdc_ref": self.pdc,
                        "readings": sorted(updated.values(), key=lambda r: r["date"]),
                    })
                except Exception as err:
                    raise UpdateFailed("Could not persist SEMERAP readings") from err
                self._archive = updated
        if not self._archive:
            raise UpdateFailed("No valid SEMERAP readings")
        return self._result()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = SemerapClient(async_get_clientsession(hass),
                           entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = SemerapCoordinator(hass, client, str(entry.data[CONF_PDC]))
    await coordinator.async_load_archive()
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_IMPORT):
        async def handle_import(call: ServiceCall) -> None:
            coordinators = list(hass.data.get(DOMAIN, {}).values())
            pdc = call.data.get(CONF_PDC)
            if pdc is not None:
                coordinators = [c for c in coordinators if c.pdc == pdc]
            if len(coordinators) != 1:
                raise HomeAssistantError(
                    "SEMERAP meter not found or ambiguous; specify pdc_ref"
                )
            count = await coordinators[0].async_import_readings(call.data["readings"])
            _LOGGER.info("Imported %s historical SEMERAP readings for %s",
                         count, coordinators[0].pdc)

        hass.services.async_register(
            DOMAIN, SERVICE_IMPORT, handle_import, schema=IMPORT_SCHEMA
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_IMPORT)
        return True
    return False
