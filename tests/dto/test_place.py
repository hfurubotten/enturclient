"""Test for place object."""
from unittest import TestCase

from enturclient.dto import Place


class PlaceTests(TestCase):
    """Test case for dto Place."""

    def setUp(self):
        """Set up test data and place object."""
        self._place_id = "NSR:StopPlace:548"
        self._place_name = "Bergen stasjon"
        self._place_estimated_calls = [{}, {}]
        self._data = {
            "id": self._place_id,
            "name": self._place_name,
            "estimatedCalls": self._place_estimated_calls,
        }
        self._place = Place(self._data, False)

    def test_parses_place_id(self):
        """Test if place id is parsed correctly."""
        self.assertEqual(self._place.place_id, self._place_id)

    def test_parses_name(self):
        """Test if name is parsed correctly."""
        self.assertEqual(self._place.name, self._place_name)

    def test_creates_estimated_calls(self):
        """Test if number of estimated calls are created."""
        self.assertEqual(
            len(self._place.estimated_calls), len(self._place_estimated_calls)
        )

    def test_parses_latitude(self):
        """Test if latitude is parsed correctly."""
        self.assertEqual(self._place.latitude, None)

    def test_parses_longitude(self):
        """Test if longitude is parsed correctly."""
        self.assertEqual(self._place.longitude, None)

    def test_parses_public_code(self):
        """Test if public code is parsed correctly."""
        self.assertEqual(self._place.public_code, None)

    def test_gives_input_out_as_raw(self):
        """Test if given input will be given out from raw property."""
        self.assertDictEqual(self._place.raw, self._data)


class PlacePlatformTests(PlaceTests):
    """Test case for dto Place."""

    def setUp(self):
        """Set up test data and place object."""
        self._place_id = "NSR:Quay:51852"
        self._place_name = "Kokstad"
        self._place_estimated_calls = [{}, {}, {}]
        self._data = {
            "id": self._place_id,
            "name": self._place_name,
            "estimatedCalls": self._place_estimated_calls,
            "publicCode": "",
            "latitude": 60.293217,
            "longitude": 5.267429,
        }
        self._place = Place(self._data, True)

    def test_parses_name(self):
        """Test if name is parsed correctly."""
        self.assertEqual(self._place.name, "Kokstad Platform 51852")

    def test_parses_latitude(self):
        """Test if latitude is parsed correctly."""
        self.assertEqual(self._place.latitude, 60.293217)

    def test_parses_longitude(self):
        """Test if longitude is parsed correctly."""
        self.assertEqual(self._place.longitude, 5.267429)

    def test_parses_public_code(self):
        """Test if public code is parsed correctly."""
        self.assertEqual(self._place.public_code, "")


class PlacePlatformWithPublicCodeTests(PlacePlatformTests):
    """Test case for dto Place."""

    def setUp(self):
        """Set up test data and place object."""
        super().setUp()
        self._data["publicCode"] = "123"
        self._place = Place(self._data, True)

    def test_parses_name(self):
        """Test if name is parsed correctly."""
        self.assertEqual(self._place.name, "Kokstad Platform 123")

    def test_parses_public_code(self):
        """Test if public code is parsed correctly."""
        self.assertEqual(self._place.public_code, "123")
