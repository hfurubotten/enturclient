"""
Real-time information about public transport departures in Norway.
"""
import requests
import logging

from enturclient.queries import *
from enturclient.dto import *

RESOURCE = 'https://api.entur.io/journey-planner/v2/graphql'
_LOGGER = logging.getLogger(__name__)


class EnturPublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(self,
                 client_name: str,
                 stops: list,
                 quays: list,
                 expand_quays: bool,
                 line_whitelist: list = None,
                 omit_non_boarding: bool = True,
                 number_of_departures: int = 2):
        """Initialize the data object."""
        self._client_name = client_name
        self._data = {}
        self.stops = stops
        self.omit_non_boarding = omit_non_boarding
        self.line_whitelist = line_whitelist
        self.number_of_departures = number_of_departures

        self.quays = quays
        if expand_quays:
            self._expand_all_quays()

        self.info = {}
        for item in stops:
            self.info[item] = Place({}, False)
        for item in quays:
            self.info[item] = Place({}, True)

        self.template_string = """query(
            $stops: [String],
            $quays: [String],
            $whitelist: InputWhiteListed,
            $numberOfDepartures: Int = 2,
            $omitNonBoarding: Boolean = true){\n"""
        if self.stops:
            self.template_string += GRAPHQL_STOP_TEMPLATE
        if self.quays:
            self.template_string += GRAPHQL_QUAY_TEMPLATE
        self.template_string += "}"
        self.template_string += GRAPHQL_CALL_FRAGMENT

    def all_stop_places_quays(self) -> list:
        """Get all stop places and quays"""
        all_places = self.stops.copy()
        for quay in self.quays:
            all_places.append(quay)
        return all_places

    def _expand_all_quays(self) -> None:
        """Find all quays from stop places."""
        if not self.stops:
            return

        headers = {'ET-Client-Name': self._client_name}
        response = requests.post(
            RESOURCE,
            json={
                'query': GRAPHQL_STOP_TO_QUAY_TEMPLATE,
                'variables': {
                    'stops': self.stops,
                    'omitNonBoarding': self.omit_non_boarding
                }
            },
            timeout=10,
            headers=headers)

        if response.status_code != 200:
            return

        result = response.json()

        if 'errors' in result:
            return

        for stop_place in result['data']['stopPlaces']:
            if len(stop_place['quays']) > 1:
                for quay in stop_place['quays']:
                    if quay['estimatedCalls']:
                        self.quays.append(quay['id'])

    def update(self) -> None:
        """Get the latest data from api.entur.org."""
        headers = {'ET-Client-Name': self._client_name}
        response = requests.post(
            RESOURCE,
            json={
                'query': self.template_string,
                'variables': {
                    'stops': self.stops,
                    'quays': self.quays,
                    'whitelist': {
                        'lines': self.line_whitelist
                    },
                    'numberOfDepartures': self.number_of_departures,
                    'omitNonBoarding': self.omit_non_boarding
                }
            },
            timeout=10,
            headers=headers)

        if response.status_code != 200:
            return

        result = response.json()

        if 'errors' in result:
            _LOGGER.warning("Entur API responded with error message: {error}",
                            result['errors'])
            return

        self._data = result['data']

        if 'stopPlaces' in self._data:
            for stop in self._data['stopPlaces']:
                self._process_place(stop, False)

        if 'quays' in self._data:
            for quay in self._data['quays']:
                self._process_place(quay, True)

    def get_stop_info(self, stop_id: str) -> Place:
        """Get all information about a stop."""
        return self.info[stop_id]

    def _process_place(self, place: dict, is_platform: bool) -> None:
        """Extract information from place dictionary."""
        place_id = place['id']
        self.info[place_id] = Place(place, is_platform)
