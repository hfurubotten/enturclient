"""Real-time information about public transport departures in Norway."""

import asyncio
import logging
from typing import Mapping, Optional

import aiohttp

import enturclient.queries as q
from enturclient import dto
from enturclient.exceptions import EnturApiError

RESOURCE = "https://api.entur.io/journey-planner/v3/graphql"
_LOGGER = logging.getLogger(__name__)


class EnturPublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(
        self,
        client_name: str,
        stops: list = None,
        quays: list = None,
        line_whitelist: list = None,
        omit_non_boarding: bool = True,
        number_of_departures: int = 2,
        web_session: aiohttp.ClientSession = None,
    ):
        """Initialize the data object."""
        if not web_session:

            async def _create_session() -> aiohttp.ClientSession:
                return aiohttp.ClientSession()

            loop = asyncio.get_event_loop()
            self.web_session = loop.run_until_complete(_create_session())
        else:
            self.web_session = web_session

        self._client_name = client_name
        self._data: dict = {}
        self.stops = stops or []
        self.quays = quays or []
        self.omit_non_boarding = omit_non_boarding
        self.line_whitelist = line_whitelist or []
        self.number_of_departures = number_of_departures

        self.info: dict = {}

    async def close_connection(self):
        """Close the aiohttp session."""
        await self.web_session.close()

    def all_stop_places_quays(self) -> list:
        """Get all stop places and quays."""
        all_places = self.stops.copy()
        for quay in self.quays:
            all_places.append(quay)
        return all_places

    async def expand_all_quays(self) -> None:
        """Find all quays from stop places."""
        if not self.stops:
            return

        headers = {"ET-Client-Name": self._client_name}
        request = {
            "query": q.GRAPHQL_STOP_TO_QUAY_QUERY,
            "variables": {
                "stops": self.stops,
                "whitelist": {"lines": self.line_whitelist},
                "omitNonBoarding": self.omit_non_boarding,
            },
        }

        result, _ = await self._async_post_json(request, headers)
        _LOGGER.debug("Got the following result from entur: %s", result)

        stop_places = _get_data(result).get("stopPlaces")
        if not isinstance(stop_places, list):
            raise EnturApiError("Invalid Journey Planner response")

        for stop_place in stop_places:
            if not isinstance(stop_place, dict):
                continue
            quays = stop_place.get("quays")
            if not isinstance(quays, list) or len(quays) <= 1:
                continue
            for quay in quays:
                if (
                    isinstance(quay, dict)
                    and quay.get("estimatedCalls")
                    and isinstance(quay.get("id"), str)
                ):
                    self.quays.append(quay["id"])

        _LOGGER.debug("Found the following queys after expansion: %s", self.quays)

    async def update(self) -> None:
        """Get the latest data from api.entur.org."""
        headers = {"ET-Client-Name": self._client_name}
        request = {
            "query": q.GRAPHQL_DEPARTURE_CALLS_QUERY,
            "variables": {
                "stops": self.stops,
                "quays": self.quays,
                "whitelist": {"lines": self.line_whitelist},
                "numberOfDepartures": self.number_of_departures,
                "omitNonBoarding": self.omit_non_boarding,
            },
        }

        result, response_headers = await self._async_post_json(request, headers)
        _LOGGER.debug("Got the following result from entur: %s", result)

        data = _get_data(result)
        stop_places = data.get("stopPlaces", [])
        quays = data.get("quays", [])
        if not isinstance(stop_places, list) or not isinstance(quays, list):
            raise EnturApiError("Invalid Journey Planner response")
        if not stop_places and not quays:
            raise EnturApiError("Journey Planner returned no stop places or quays")
        self._data = data

        if "stopPlaces" in self._data:
            for stop in stop_places:
                self._process_place(stop, False)

        if "quays" in self._data:
            for quay in quays:
                self._process_place(quay, True)

        # find rate limits
        rate_limit_allowed = response_headers.get("Rate-Limit-Allowed")
        rate_limit_available = response_headers.get("Rate-Limit-Available")
        rate_limit_expiry_time = response_headers.get("Rate-Limit-Expiry-Time")
        rate_limit_range = response_headers.get("Rate-Limit-Range")
        rate_limit_used = response_headers.get("Rate-Limit-Used")
        _LOGGER.debug(
            "Used %s of total %s in rate limits. Still %s available "
            "within time unit %s. Rate limit expires at %s.",
            rate_limit_used,
            rate_limit_allowed,
            rate_limit_available,
            rate_limit_range,
            rate_limit_expiry_time,
        )

    async def _async_post_json(
        self, request: dict, headers: dict[str, str]
    ) -> tuple[dict, Mapping[str, str]]:
        """Post a Journey Planner request and normalize transport errors."""
        try:
            async with asyncio.timeout(15):
                async with self.web_session.post(
                    RESOURCE, json=request, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    response_headers = resp.headers
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise EnturApiError from err

        if not isinstance(result, dict):
            raise EnturApiError("Invalid Journey Planner response")
        return result, response_headers

    def get_stop_info(self, stop_id: str) -> Optional[dto.Place]:
        """Get all information about a stop."""
        return self.info.get(stop_id)

    def _process_place(self, place: dict, is_platform: bool) -> None:
        """Extract information from place dictionary."""
        place_id = place["id"]
        self.info[place_id] = dto.Place(place, is_platform)


def _get_data(result: dict) -> dict:
    """Validate the GraphQL envelope and return its data payload."""
    if result.get("errors"):
        raise EnturApiError("Journey Planner returned GraphQL errors")
    data = result.get("data")
    if not isinstance(data, dict):
        raise EnturApiError("Invalid Journey Planner response")
    return data
