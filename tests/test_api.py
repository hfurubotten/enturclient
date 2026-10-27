"""Tests for the Journey Planner data client."""

from typing import Self
from unittest import IsolatedAsyncioTestCase

from aiohttp import ClientResponseError

from enturclient import EnturApiError, EnturPublicTransportData


class _Response:
    def __init__(self, payload: object, status_error: Exception | None = None) -> None:
        self.payload = payload
        self.status_error = status_error
        self.headers: dict[str, str] = {}

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_error:
            raise self.status_error

    async def json(self) -> object:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class _Session:
    def __init__(self, response: _Response) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> _Response:
        self.calls.append(kwargs)
        return self.response


class EnturPublicTransportDataTests(IsolatedAsyncioTestCase):
    async def test_update_requests_stop_place_coordinates(self) -> None:
        """Request coordinates so stop-place sensors can be shown on maps."""
        stop_id = "NSR:StopPlace:1"
        session = _Session(
            _Response(
                {
                    "data": {
                        "stopPlaces": [
                            {
                                "id": stop_id,
                                "name": "Test stop",
                                "latitude": 60.293217,
                                "longitude": 5.267429,
                                "estimatedCalls": [],
                            }
                        ]
                    }
                }
            )
        )
        client = EnturPublicTransportData(
            "test", stops=[stop_id], web_session=session  # type: ignore[arg-type]
        )

        await client.update()

        stop = client.get_stop_info(stop_id)
        self.assertEqual(stop.latitude, 60.293217)
        self.assertEqual(stop.longitude, 5.267429)
        query = session.calls[0]["json"]["query"]  # type: ignore[index]
        self.assertIn("latitude", query)
        self.assertIn("longitude", query)

    async def test_update_processes_stop_places(self) -> None:
        stop_id = "NSR:StopPlace:1"
        client = EnturPublicTransportData(
            "test",
            stops=[stop_id],
            web_session=_Session(
                _Response(
                    {
                        "data": {
                            "stopPlaces": [
                                {
                                    "id": stop_id,
                                    "name": "Test stop",
                                    "estimatedCalls": [],
                                }
                            ]
                        }
                    }
                )
            ),  # type: ignore[arg-type]
        )

        await client.update()

        self.assertEqual(client.get_stop_info(stop_id).name, "Test stop")

    async def test_update_raises_api_error_for_http_error(self) -> None:
        response = _Response({}, ClientResponseError(None, (), status=503))
        client = EnturPublicTransportData(
            "test",
            stops=["NSR:StopPlace:1"],
            web_session=_Session(response),  # type: ignore[arg-type]
        )

        with self.assertRaises(EnturApiError):
            await client.update()

    async def test_update_raises_api_error_for_invalid_json(self) -> None:
        client = EnturPublicTransportData(
            "test",
            stops=["NSR:StopPlace:1"],
            web_session=_Session(_Response(ValueError("invalid JSON"))),  # type: ignore[arg-type]
        )

        with self.assertRaises(EnturApiError):
            await client.update()

    async def test_update_raises_api_error_for_graphql_errors(self) -> None:
        client = EnturPublicTransportData(
            "test",
            stops=["NSR:StopPlace:1"],
            web_session=_Session(_Response({"errors": [{"message": "unavailable"}]})),  # type: ignore[arg-type]
        )

        with self.assertRaises(EnturApiError):
            await client.update()

    async def test_expand_quays_raises_api_error_for_graphql_errors(self) -> None:
        client = EnturPublicTransportData(
            "test",
            stops=["NSR:StopPlace:1"],
            web_session=_Session(_Response({"errors": [{"message": "unavailable"}]})),  # type: ignore[arg-type]
        )

        with self.assertRaises(EnturApiError):
            await client.expand_all_quays()
