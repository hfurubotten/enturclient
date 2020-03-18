"""Data transfer object for estimated call object."""
from datetime import datetime, timedelta


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
        """Calculate delay in minutes."""
        return int(self.delay.total_seconds() / 60)

    @property
    def delay(self) -> timedelta:
        """Calculate delay."""
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
