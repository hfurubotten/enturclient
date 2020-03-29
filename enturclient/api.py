"""Real-time information about public transport departures in Norway."""
import asyncio
import logging
from typing import Optional

import aiohttp
import async_timeout

import enturclient.dto as dto
import enturclient.queries as q

RESOURCE = "https://api.entur.io/journey-planner/v2/graphql"
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

    def get_gql_query(self):
        """Generate GraphQL query."""
        template_string = """query(
            $stops: [String],
            $quays: [String],
            $whitelist: InputWhiteListed,
            $numberOfDepartures: Int = 2,
            $omitNonBoarding: Boolean = true){\n"""
        if self.stops:
            template_string += q.GRAPHQL_STOP_TEMPLATE
        if self.quays:
            template_string += q.GRAPHQL_QUAY_TEMPLATE
        template_string += "}"
        template_string += q.GRAPHQL_CALL_FRAGMENT

        return template_string

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
            "query": q.GRAPHQL_STOP_TO_QUAY_TEMPLATE,
            "variables": {
                "stops": self.stops,
                "whitelist": {"lines": self.line_whitelist},
                "omitNonBoarding": self.omit_non_boarding,
            },
        }

        with async_timeout.timeout(10):
            async with self.web_session.post(
                RESOURCE, json=request, headers=headers
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        "Error connecting to Entur, response http status code: %s",
                        resp.status,
                    )
                    return
                result = await resp.json()

        if "errors" in result:
            return

        for stop_place in result["data"]["stopPlaces"]:
            if len(stop_place["quays"]) > 1:
                for quay in stop_place["quays"]:
                    if quay["estimatedCalls"]:
                        self.quays.append(quay["id"])

    async def update(self) -> None:
        """Get the latest data from api.entur.org."""
        headers = {"ET-Client-Name": self._client_name}
        request = {
            "query": self.get_gql_query(),
            "variables": {
                "stops": self.stops,
                "quays": self.quays,
                "whitelist": {"lines": self.line_whitelist},
                "numberOfDepartures": self.number_of_departures,
                "omitNonBoarding": self.omit_non_boarding,
            },
        }

        with async_timeout.timeout(10):
            async with self.web_session.post(
                RESOURCE, json=request, headers=headers
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        "Error connecting to Entur, response http status code: %s",
                        resp.status,
                    )
                    return
                result = await resp.json()

        if "errors" in result:
            _LOGGER.warning(
                "Entur API responded with error message: %s", result["errors"]
            )
            return

        self._data = result["data"]

        if "stopPlaces" in self._data:
            for stop in self._data["stopPlaces"]:
                self._process_place(stop, False)

        if "quays" in self._data:
            for quay in self._data["quays"]:
                self._process_place(quay, True)

        # find rate limits
        rate_limit_allowed = resp.headers.get("Rate-Limit-Allowed")
        rate_limit_available = resp.headers.get("Rate-Limit-Available")
        rate_limit_expiry_time = resp.headers.get("Rate-Limit-Expiry-Time")
        rate_limit_range = resp.headers.get("Rate-Limit-Range")
        rate_limit_used = resp.headers.get("Rate-Limit-Used")
        _LOGGER.debug(
            "Used %s of total %s in rate limits. Still %s available for use within time unit %s. Current rate limit expire at %s.",
            rate_limit_used,
            rate_limit_allowed,
            rate_limit_available,
            rate_limit_range,
            rate_limit_expiry_time,
        )

    def get_stop_info(self, stop_id: str) -> Optional[dto.Place]:
        """Get all information about a stop."""
        return self.info.get(stop_id)

    def _process_place(self, place: dict, is_platform: bool) -> None:
        """Extract information from place dictionary."""
        place_id = place["id"]
        self.info[place_id] = dto.Place(place, is_platform)
