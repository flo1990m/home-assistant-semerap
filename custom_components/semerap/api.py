"""SEMERAP customer portal API client (unofficial)."""
from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE, ORIGIN


class SemerapError(Exception):
    """An API request failed."""


class SemerapAuthError(SemerapError):
    """Credentials were rejected."""


class SemerapClient:
    """Authenticate and read account metering statements."""

    def __init__(self, session: ClientSession, login: str, password: str) -> None:
        self._session = session
        self._login = login
        self._password = password
        self._token: str | None = None
        self._lock = asyncio.Lock()

    async def _request(self, method: str, path: str, *, payload: dict | None = None,
                       authorized: bool = True) -> Any:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": ORIGIN,
            "Referer": ORIGIN + "/",
            "User-Agent": "Mozilla/5.0",
        }
        if authorized and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            async with self._session.request(
                method, API_BASE + path, headers=headers, json=payload, timeout=20,
                allow_redirects=False,
            ) as response:
                if response.status in (401, 403):
                    raise SemerapAuthError(f"Authentication rejected ({response.status})")
                response.raise_for_status()
                data = await response.json(content_type=None)
                return data
        except SemerapAuthError:
            raise
        except (ClientResponseError, ClientError, asyncio.TimeoutError, ValueError) as err:
            raise SemerapError(f"SEMERAP API request failed: {type(err).__name__}") from err

    async def login(self) -> None:
        async with self._lock:
            await self._authenticate()

    async def _authenticate(self) -> None:
        data = await self._request(
            "POST", "/auth", payload={"login": self._login, "password": self._password},
            authorized=False,
        )
        token = data.get("token") if isinstance(data, dict) else None
        if not isinstance(token, str) or not token:
            raise SemerapAuthError("Authentication returned no token")
        self._token = token

    async def get(self, path: str) -> Any:
        if not self._token:
            await self.login()
        try:
            return await self._request("GET", path)
        except SemerapAuthError:
            await self.login()
            return await self._request("GET", path)

    async def pdcs(self) -> list[dict]:
        result = await self.get("/pdcs")
        if not isinstance(result, list):
            raise SemerapError("Unexpected metering points response")
        return [x for x in result if isinstance(x, dict) and x.get("pdcRef") is not None]

    async def statements(self, pdc_ref: str) -> list[dict]:
        result = await self.get("/statements?" + urlencode({"pdcRef": pdc_ref}))
        if not isinstance(result, list):
            raise SemerapError("Unexpected statements response")
        return [x for x in result if isinstance(x, dict) and x.get("date")]
