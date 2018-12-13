"""
Real-time information about public transport departures in Norway.
"""
from datetime import datetime, timedelta
from string import Template

import requests

from enturclient.queries import *
from enturclient.consts import *

RESOURCE = 'https://api.entur.org/journeyplanner/2.0/index/graphql'


class EnturPublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(self, client_name: str, stops: list, quays: list, expand_quays: bool):
        """Initialize the data object."""
        self._client_name = client_name
        self._data = {}
        self.stops = stops
        self.stops_string = "\"" + "\",\"".join(stops) + "\""

        self.quays = quays
        if expand_quays:
            self._expand_all_quays()

        self.quays_string = "\"" + "\",\"".join(self.quays) + "\""

        self.info = {}
        for item in stops:
            self.info[item] = {}
        for item in quays:
            self.info[item] = {}

        self.template_string = "{\n"
        if self.stops:
            self.template_string += GRAPHQL_STOP_TEMPLATE
        if self.quays:
            self.template_string += GRAPHQL_QUAY_TEMPLATE
        self.template_string += "}"
        self.template = Template(self.template_string)

    def all_stop_places_quays(self) -> list:
        """Get all stop places and quays"""
        all = self.stops.copy()
        for quay in self.quays:
            all.append(quay)
        return all

    def _expand_all_quays(self) -> None:
        """Find all quays from stop places."""
        if not self.stops_string:
            return

        query = Template(GRAPHQL_STOP_TO_QUAY_TEMPLATE).substitute(
            stops=self.stops_string,
            time=datetime.utcnow().strftime("%Y-%m-%dT%XZ"))
        headers = {'ET-Client-Name': self._client_name}
        response = requests.post(
            RESOURCE,
            json={"query": query},
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
        query = self.template.substitute(
            stops=self.stops_string,
            quays=self.quays_string,
            time=datetime.utcnow().strftime("%Y-%m-%dT%XZ"))
        headers = {'ET-Client-Name': self._client_name}
        response = requests.post(
            RESOURCE,
            json={"query": query},
            timeout=10,
            headers=headers)

        if response.status_code != 200:
            return

        result = response.json()

        if 'errors' in result:
            return

        self._data = result['data']

        if 'stopPlaces' in self._data:
            for stop in self._data['stopPlaces']:
                self._process_place(stop, False)

        if 'quays' in self._data:
            for quey in self._data['quays']:
                self._process_place(quey, True)

    def get_stop_info(self, id: str) -> dict:
        """Get all information about a stop."""
        return self.info[id]

    def _process_place(self, place: dict, is_platform: bool) -> None:
        """Extract information from place dictionary."""
        place_id = place['id']
        name = place['name']
        if is_platform:
            if place["publicCode"]:
                name = name + " Platform " + place["publicCode"]
            else:
                name = name + " Platform " + place_id.split(':')[-1]

        info = {ATTR_STOP_ID: place_id,
                CONF_NAME: name}

        if is_platform:
            info[CONF_LOCATION] = {}
            info[CONF_LOCATION][CONF_LATITUDE] = place['latitude']
            info[CONF_LOCATION][CONF_LONGITUDE] = place['longitude']

        info[CONF_TRANSPORT_MODE] = self._get_transport_mode(place)

        attributes = {}

        if place['estimatedCalls']:
            call = place['estimatedCalls'][0]
            attributes[ATTR_EXPECTED_AT] = call['expectedDepartureTime']
            attributes[ATTR_REALTIME] = call['realtime']
            attributes[ATTR_ROUTE] = self._get_route_text(call)
            attributes[ATTR_DELAY] = self._get_call_delay(call)
        if len(place['estimatedCalls']) > 1:
            call = place['estimatedCalls'][1]
            attributes[ATTR_NEXT_UP_AT] = call['expectedDepartureTime']
            attributes[ATTR_NEXT_UP_REALTIME] = call['realtime']
            attributes[ATTR_NEXT_UP_ROUTE] = self._get_route_text(call)
            attributes[ATTR_NEXT_UP_DELAY] = self._get_call_delay(call)
        info[ATTR] = attributes
        self.info[place_id] = info

    def _get_transport_mode(self, place: dict) -> str:
        if place['estimatedCalls']:
            return place['estimatedCalls'][0]['serviceJourney']['journeyPattern']['line']['transportMode']
        else:
            return UNKNOWN

    def _get_route_text(self, call: dict) -> str:
        return call['serviceJourney']['journeyPattern']['line']['publicCode'] \
            + " " + call['destinationDisplay']['frontText']

    def _get_call_delay(self, call: dict) -> str:
        return self._time_diff_in_minutes(
            call['expectedDepartureTime'],
            call['aimedDepartureTime'])

    def _time_diff_in_minutes(self, timestamp1: str, timestamp2: str) -> str:
        """Get the time in minutes from a timestamp.

        The timestamp should be in the format
        year-month-yearThour:minute:second+timezone
        """
        if timestamp1 is None:
            return UNKNOWN
        if timestamp2 is None:
            return UNKNOWN

        time1 = datetime.strptime(timestamp1, "%Y-%m-%dT%H:%M:%S%z")
        time2 = datetime.strptime(timestamp2, "%Y-%m-%dT%H:%M:%S%z")
        diff = time1 - time2

        return str(int(diff.total_seconds() / 60))

