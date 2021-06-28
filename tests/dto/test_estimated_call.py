"""Test for estimated calls object."""
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from enturclient.dto import EstimatedCall


class EstimatedClassTests(TestCase):
    """Test case for dto EstimatedCall."""

    def setUp(self):
        """Set up test data and estimated call."""
        self._data = {
            "realtime": True,
            "aimedArrivalTime": "2020-03-15T21:57:00+0100",
            "aimedDepartureTime": "2020-03-15T21:58:00+0100",
            "expectedArrivalTime": "2020-03-15T22:56:00+0100",
            "expectedDepartureTime": "2020-03-15T22:59:05+0100",
            "destinationDisplay": {"frontText": "Voss"},
            "serviceJourney": {
                "journeyPattern": {
                    "line": {
                        "id": "NSB:Line:45",
                        "transportMode": "rail",
                        "publicCode": "45",
                    }
                }
            },
        }
        self._estimated_call = EstimatedCall(self._data)

    def test_parses_realtime_property(self):
        """Test if realtime is parsed correctly."""
        self.assertTrue(self._estimated_call.is_realtime)

    def test_parses_aimed_arrival_time(self):
        """Test if aimed arrival time is parsed correctly."""
        self.assertEqual(
            self._estimated_call.aimed_arrival_time,
            datetime(2020, 3, 15, 21, 57, 0, 0, timezone(timedelta(hours=1))),
        )

    def test_parses_expected_arrival_time(self):
        """Test if expected arrival time is parsed correctly."""
        self.assertEqual(
            self._estimated_call.expected_arrival_time,
            datetime(2020, 3, 15, 22, 56, 0, 0, timezone(timedelta(hours=1))),
        )

    def test_parses_aimed_departure_time(self):
        """Test if aimed departure time is parsed correctly."""
        self.assertEqual(
            self._estimated_call.aimed_departure_time,
            datetime(2020, 3, 15, 21, 58, 0, 0, timezone(timedelta(hours=1))),
        )

    def test_parses_expected_departure_time(self):
        """Test if expected departure time is parsed correctly."""
        self.assertEqual(
            self._estimated_call.expected_departure_time,
            datetime(2020, 3, 15, 22, 59, 5, 0, timezone(timedelta(hours=1))),
        )

    def test_parses_transport_mode(self):
        """Test if transport mode is parsed correctly."""
        self.assertEqual(self._estimated_call.transport_mode, "rail")

    def test_calculates_delay_in_min(self):
        """Test if EstimatedCall calculates delay in minutes correctly."""
        self.assertEqual(self._estimated_call.delay_in_min, 61)

    def test_calculates_delay(self):
        """Test if EstimatedCall calculates delay correctly."""
        self.assertEqual(self._estimated_call.delay, timedelta(seconds=3665))

    def test_parses_line_id(self):
        """Test if EstimatedCall parses input to give correct line id."""
        self.assertEqual(self._estimated_call.line_id, "NSB:Line:45")

    def test_parses_line_public_code(self):
        """Test if EstimatedCall parses input to give correct line public code."""
        self.assertEqual(self._estimated_call.line_public_code, "45")

    def test_parses_front_display(self):
        """Test if EstimatedCall parses input to give correct front display."""
        self.assertEqual(self._estimated_call.front_display, "45 Voss")

    def test_gives_input_out_as_raw(self):
        """Test if given input will be given out from raw property."""
        self.assertDictEqual(self._estimated_call.raw, self._data)
