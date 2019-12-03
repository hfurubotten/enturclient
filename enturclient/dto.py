from datetime import datetime, timedelta


class Place:
    """Represents a stop place or platform from entur."""

    def __init__(self, data: dict, is_platform: bool):
        """Initialize the place object."""
        self._data = data
        self.is_platform = is_platform

    @property
    def place_id(self) -> str:
        """Id for the stop place or platform."""
        return self._data["id"]

    @property
    def name(self) -> str:
        """Friendly name for the stop place or platform"""
        if self.is_platform:
            if self._data["publicCode"]:
                return self._data["name"] + " Platform " + self._data["publicCode"]
            else:
                return self._data["name"] + " Platform " + self.place_id.split(":")[-1]
        else:
            return self._data["name"]

    @property
    def latitude(self) -> float:
        """Latitude part of place location."""
        return self._data.get("latitude")

    @property
    def longitude(self) -> float:
        """Longitude part of place location."""
        return self._data.get("longitude")

    @property
    def public_code(self) -> int:
        return self._data.get("publicCode")

    @property
    def estimated_calls(self):
        """List estimated calls from the place."""
        return [EstimatedCall(s) for s in self._data["estimatedCalls"]]

    @property
    def raw(self):
        """Raw data for the place from the API."""
        return self._data


class EstimatedCall:
    """Estimated call data."""

    def __init__(self, data: dict):
        """Initialize the estimated call object."""
        self._data = data

    @property
    def is_realtime(self) -> bool:
        """If the call is in real time."""
        return bool(self._data["realtime"])

    @property
    def aimed_arrival_time(self) -> datetime:
        """Aimed arrival time for the call according to the time table."""
        return datetime.strptime(self._data["aimedArrivalTime"], "%Y-%m-%dT%H:%M:%S%z")

    @property
    def expected_arrival_time(self) -> datetime:
        """Expected arrival time from realtime reports."""
        return datetime.strptime(
            self._data["expectedArrivalTime"], "%Y-%m-%dT%H:%M:%S%z"
        )

    @property
    def aimed_departure_time(self) -> datetime:
        """Aimed departure time for the call according to the time table."""
        return datetime.strptime(
            self._data["aimedDepartureTime"], "%Y-%m-%dT%H:%M:%S%z"
        )

    @property
    def expected_departure_time(self) -> datetime:
        """Expected departure time from realtime reports."""
        return datetime.strptime(
            self._data["expectedDepartureTime"], "%Y-%m-%dT%H:%M:%S%z"
        )

    @property
    def transport_mode(self) -> str:
        """Mode of transport."""
        return self._data["serviceJourney"]["journeyPattern"]["line"]["transportMode"]

    @property
    def delay_in_min(self) -> int:
        """Calculated delay in minutes."""
        return int(self.delay.total_seconds() / 60)

    @property
    def delay(self) -> timedelta:
        """Calculated delay."""
        return self.expected_departure_time - self.aimed_departure_time

    @property
    def line_id(self) -> str:
        """Id for the line driving the call."""
        return self._data["serviceJourney"]["journeyPattern"]["line"]["id"]

    @property
    def line_public_code(self) -> str:
        """Public id for the line driving the call."""
        return self._data["serviceJourney"]["journeyPattern"]["line"]["publicCode"]

    @property
    def front_display(self) -> str:
        """Text shown in front of the transport."""
        return "{} {}".format(
            self.line_public_code, self._data["destinationDisplay"]["frontText"]
        )

    @property
    def raw(self):
        """Raw data for the place from the API."""
        return self._data
