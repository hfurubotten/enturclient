"""Data transfer object for Place object."""
from typing import Optional

from .estimated_call import EstimatedCall


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
        """Friendly name for the stop place or platform."""
        if self.is_platform:
            if self.public_code:
                return self._data["name"] + " Platform " + self.public_code
            return self._data["name"] + " Platform " + self.place_id.split(":")[-1]

        return self._data["name"]

    @property
    def latitude(self) -> Optional[float]:
        """Latitude part of place location."""
        return self._data.get("latitude")

    @property
    def longitude(self) -> Optional[float]:
        """Longitude part of place location."""
        return self._data.get("longitude")

    @property
    def public_code(self) -> Optional[int]:
        """Public code for the stop place."""
        return self._data.get("publicCode")

    @property
    def estimated_calls(self):
        """List estimated calls from the place."""
        return [EstimatedCall(s) for s in self._data["estimatedCalls"]]

    @property
    def raw(self):
        """Raw data for the place from the API."""
        return self._data
