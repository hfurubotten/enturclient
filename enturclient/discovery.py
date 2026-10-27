"""Discovery API client for Entur stop places, routes, and quays."""

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientSession

from enturclient.api import RESOURCE
from enturclient.exceptions import EnturApiError
from enturclient.queries import (
    DISCOVERY_STOP_PLACE_LINES_QUERY,
    DISCOVERY_STOP_PLACE_QUAYS_QUERY,
)

GEOCODER_AUTOCOMPLETE_URL = "https://api.entur.io/geocoder/v3/autocomplete"
GEOCODER_PLACE_URL = "https://api.entur.io/geocoder/v3/place"
JOURNEY_PLANNER_URL = RESOURCE
STOP_PLACE_URL = "https://entur.no/nearby-stop-place-detail?id={}"

STOP_PLACE_TYPE_ICONS = {
    "airport": "✈️",
    "busStation": "🚌",
    "busPlatform": "🚏",
    "coachStation": "🚌",
    "ferryPort": "⚓",
    "ferryStop": "⛴️",
    "harbourPort": "⚓",
    "liftStation": "🚡",
    "metroStation": "🚇",
    "onstreetBus": "🚏",
    "onstreetTram": "🚋",
    "other": "🚉",
    "railStation": "🚆",
    "taxiRank": "🚕",
    "tramStation": "🚋",
    "vehicleRailInterchange": "🚗",
}


@dataclass(frozen=True, slots=True)
class EnturStopPlace:
    """A stop place returned by the Entur Geocoder."""

    stop_id: str
    name: str
    display_name: str
    locality: str
    transport_modes: tuple[str, ...]
    role: str
    stop_place_types: tuple[str, ...] = ()

    @property
    def selection_label(self) -> str:
        """Return a context-rich label for a stop place."""
        details = [self.display_name]
        if (
            self.locality
            and self.locality.casefold() not in self.display_name.casefold()
        ):
            details.append(self.locality)
        if self.transport_modes:
            details.append(", ".join(self.transport_modes))
        return " · ".join(details)

    @property
    def entur_url(self) -> str:
        """Return the Entur departure board URL for the stop place."""
        return STOP_PLACE_URL.format(quote(self.stop_id, safe=""))

    @property
    def type_icons(self) -> str:
        """Return icons for the stop place types supplied by Entur."""
        icons = dict.fromkeys(
            STOP_PLACE_TYPE_ICONS.get(stop_place_type, "🚉")
            for stop_place_type in self.stop_place_types
        )
        return " ".join(icons) or "🚏"


@dataclass(frozen=True, slots=True)
class EnturRoute:
    """A route serving an Entur stop place."""

    line_id: str
    public_code: str
    transport_mode: str
    name: str | None = None

    @property
    def operator_code(self) -> str:
        """Return the authority code from the Entur line ID."""
        authority, separator, _ = self.line_id.partition(":Line:")
        return authority if separator else ""

    @property
    def technical_id(self) -> str:
        """Return the line ID in a compact, user-readable form."""
        authority, separator, line_code = self.line_id.partition(":Line:")
        if not separator:
            return self.line_id
        return f"{line_code}-{authority}"

    @property
    def selection_label(self) -> str:
        """Return a user-friendly route label."""
        public_code = self.public_code
        if "_" in public_code and self.name:
            name_code = self.name.split(maxsplit=1)[0]
            if name_code:
                public_code = name_code
        route_label = (
            " ".join(part for part in (public_code, self.operator_code) if part)
            or self.line_id
        )
        if self.technical_id != self.line_id:
            route_label += f" ({self.technical_id})"
        return route_label


@dataclass(frozen=True, slots=True)
class EnturQuay:
    """A quay/platform belonging to an Entur stop place."""

    quay_id: str
    name: str
    public_code: str | None

    @property
    def selection_label(self) -> str:
        """Return a concise label for a platform selector."""
        if self.public_code:
            return f"{self.public_code} · {self.name}"
        return self.name


class EnturDiscoveryClient:
    """Fetch and parse Entur Geocoder and Journey Planner discovery data."""

    def __init__(self, client_name: str, web_session: ClientSession) -> None:
        """Initialize the client with an application name and shared session."""
        self._headers = {"ET-Client-Name": client_name}
        self._web_session = web_session

    async def async_search_stop_places(self, query: str) -> tuple[EnturStopPlace, ...]:
        """Search Entur stop places by name."""
        payload = await self._async_get_json(
            GEOCODER_AUTOCOMPLETE_URL,
            params={
                "q": query,
                "lang": "no",
                "limit": 10,
                "layers": "stopPlace",
                "multimodal": "parent",
            },
        )
        return _parse_stop_places(payload)

    async def async_get_stop_place(self, stop_id: str) -> EnturStopPlace:
        """Return one stop place from the Geocoder by its canonical ID."""
        payload = await self._async_get_json(
            GEOCODER_PLACE_URL, params={"ids": stop_id, "lang": "no"}
        )
        try:
            return next(
                place
                for place in _parse_stop_places(payload)
                if place.stop_id == stop_id
            )
        except StopIteration as err:
            raise EnturApiError("Stop place was not returned by Entur") from err

    async def async_get_stop_routes(self, stop_id: str) -> tuple[EnturRoute, ...]:
        """Return routes currently serving a stop place."""
        payload = await self._async_post_json(
            {
                "query": DISCOVERY_STOP_PLACE_LINES_QUERY,
                "variables": {"stopPlaceId": stop_id, "numberOfDepartures": 50},
            }
        )
        return _parse_stop_routes(payload)

    async def async_get_stop_quays(self, stop_id: str) -> tuple[EnturQuay, ...]:
        """Return active quays/platforms belonging to a stop place."""
        payload = await self._async_post_json(
            {
                "query": DISCOVERY_STOP_PLACE_QUAYS_QUERY,
                "variables": {"stopPlaceId": stop_id},
            }
        )
        return _parse_stop_quays(payload)

    async def _async_get_json(self, url: str, *, params: dict[str, Any]) -> Any:
        """Fetch JSON from an Entur HTTP endpoint."""
        try:
            async with asyncio.timeout(15):
                async with self._web_session.get(
                    url, params=params, headers=self._headers
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise EnturApiError from err

    async def _async_post_json(self, request: dict[str, Any]) -> Any:
        """Post a Journey Planner GraphQL request and return its JSON body."""
        try:
            async with asyncio.timeout(15):
                async with self._web_session.post(
                    RESOURCE,
                    json=request,
                    headers={**self._headers, "Content-Type": "application/json"},
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise EnturApiError from err


def _parse_stop_places(payload: Any) -> tuple[EnturStopPlace, ...]:
    """Parse Geocoder v1 stop place results."""
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise EnturApiError("Invalid Geocoder response")

    places = []
    for feature in payload["features"]:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            continue

        stop_id = properties.get("id")
        if not isinstance(stop_id, str) or not stop_id.startswith("NSR:StopPlace:"):
            continue

        names = properties.get("names")
        names = names if isinstance(names, dict) else {}
        name = names.get("default") or names.get("display") or stop_id
        name = name if isinstance(name, str) else stop_id
        display_name = names.get("display") or name
        display_name = display_name if isinstance(display_name, str) else name

        address = properties.get("address")
        address = address if isinstance(address, dict) else {}
        locality = address.get("locality") or ""
        locality = locality if isinstance(locality, str) else ""

        modes = properties.get("transportModes")
        transport_modes = (
            tuple(
                mode["mode"]
                for mode in modes
                if isinstance(mode, dict) and isinstance(mode.get("mode"), str)
            )
            if isinstance(modes, list)
            else ()
        )

        role = properties.get("stopPlaceRole", "standalone")
        role = role if isinstance(role, str) else "standalone"
        types = properties.get("stopPlaceTypes")
        stop_place_types = (
            tuple(value for value in types if isinstance(value, str))
            if isinstance(types, list)
            else ()
        )
        places.append(
            EnturStopPlace(
                stop_id,
                name,
                display_name,
                locality,
                transport_modes,
                role,
                stop_place_types,
            )
        )
    return tuple(places)


def _parse_stop_routes(payload: Any) -> tuple[EnturRoute, ...]:
    """Parse routes from a Journey Planner response."""
    if not isinstance(payload, dict) or payload.get("errors"):
        raise EnturApiError("Invalid Journey Planner response")
    data = payload.get("data")
    stop_places = data.get("stopPlaces") if isinstance(data, dict) else None
    if not isinstance(stop_places, list):
        raise EnturApiError("Invalid Journey Planner response")

    routes: dict[str, EnturRoute] = {}
    for stop_place in stop_places:
        if not isinstance(stop_place, dict):
            continue
        calls = stop_place.get("estimatedCalls")
        if not isinstance(calls, list):
            continue
        for call in calls:
            if not isinstance(call, dict):
                continue
            journey = call.get("serviceJourney")
            pattern = (
                journey.get("journeyPattern") if isinstance(journey, dict) else None
            )
            line = pattern.get("line") if isinstance(pattern, dict) else None
            if not isinstance(line, dict):
                continue
            line_id = line.get("id")
            public_code = line.get("publicCode")
            transport_mode = line.get("transportMode")
            name = line.get("name")
            if (
                not isinstance(line_id, str)
                or not isinstance(public_code, str)
                or not isinstance(transport_mode, str)
            ):
                continue
            routes.setdefault(
                line_id,
                EnturRoute(
                    line_id,
                    public_code,
                    transport_mode,
                    name if isinstance(name, str) else None,
                ),
            )
    return tuple(routes.values())


def _parse_stop_quays(payload: Any) -> tuple[EnturQuay, ...]:
    """Parse active quays from a Journey Planner response."""
    if not isinstance(payload, dict) or payload.get("errors"):
        raise EnturApiError("Invalid Journey Planner response")
    data = payload.get("data")
    stop_places = data.get("stopPlaces") if isinstance(data, dict) else None
    if not isinstance(stop_places, list):
        raise EnturApiError("Invalid Journey Planner response")

    quays: dict[str, EnturQuay] = {}
    for stop_place in stop_places:
        if not isinstance(stop_place, dict):
            continue
        values = stop_place.get("quays")
        if not isinstance(values, list):
            continue
        for quay in values:
            if not isinstance(quay, dict):
                continue
            quay_id = quay.get("id")
            name = quay.get("name")
            public_code = quay.get("publicCode")
            if not isinstance(quay_id, str) or not isinstance(name, str):
                continue
            quays.setdefault(
                quay_id,
                EnturQuay(
                    quay_id,
                    name,
                    public_code if isinstance(public_code, str) else None,
                ),
            )
    return tuple(quays.values())
