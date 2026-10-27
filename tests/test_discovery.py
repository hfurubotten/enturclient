"""Tests for Entur discovery API support."""

from typing import Self
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from aiohttp import ClientResponseError

from enturclient import (
    EnturApiError,
    EnturDiscoveryClient,
    EnturQuay,
    EnturRoute,
    EnturStopPlace,
)
from enturclient.discovery import (
    GEOCODER_AUTOCOMPLETE_URL,
    GEOCODER_PLACE_URL,
    _parse_stop_places,
    _parse_stop_quays,
    _parse_stop_routes,
)
from enturclient.queries import (
    DISCOVERY_STOP_PLACE_LINES_QUERY,
    DISCOVERY_STOP_PLACE_QUAYS_QUERY,
)


class _Response:
    def __init__(self, payload: object, status_error: Exception | None = None) -> None:
        self.payload = payload
        self.status_error = status_error

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
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> _Response:
        self.calls.append(("GET", url, kwargs))
        return self.response

    def post(self, url: str, **kwargs: object) -> _Response:
        self.calls.append(("POST", url, kwargs))
        return self.response


class EnturDiscoveryClientTests(IsolatedAsyncioTestCase):
    async def test_search_stop_places(self) -> None:
        session = _Session(
            _Response(
                {
                    "features": [
                        {
                            "properties": {
                                "id": "NSR:StopPlace:548",
                                "names": {
                                    "default": "Bergen busstasjon",
                                    "display": "Bergen busstasjon, Bergen",
                                },
                                "address": {"locality": "Bergen"},
                                "transportModes": [{"mode": "bus"}, {"mode": "rail"}],
                                "stopPlaceTypes": ["busStation", "railStation"],
                                "stopPlaceRole": "parent",
                            }
                        },
                        {"properties": {"id": "NSR:Quay:1"}},
                    ]
                }
            )
        )
        client = EnturDiscoveryClient("test-client", session)  # type: ignore[arg-type]

        places = await client.async_search_stop_places("Bergen")

        self.assertEqual(
            places,
            (
                EnturStopPlace(
                    "NSR:StopPlace:548",
                    "Bergen busstasjon",
                    "Bergen busstasjon, Bergen",
                    "Bergen",
                    ("bus", "rail"),
                    "parent",
                    ("busStation", "railStation"),
                ),
            ),
        )
        self.assertEqual(
            places[0].selection_label, "Bergen busstasjon, Bergen · bus, rail"
        )
        self.assertEqual(places[0].type_icons, "🚌 🚆")
        method, url, request = session.calls[0]
        self.assertEqual((method, url), ("GET", GEOCODER_AUTOCOMPLETE_URL))
        self.assertEqual(
            request["params"],
            {
                "q": "Bergen",
                "lang": "no",
                "limit": 10,
                "layers": "stopPlace",
                "multimodal": "parent",
            },
        )
        self.assertEqual(request["headers"], {"ET-Client-Name": "test-client"})

    async def test_get_stop_place(self) -> None:
        session = _Session(
            _Response(
                {
                    "features": [
                        {
                            "properties": {
                                "id": "NSR:StopPlace:548",
                                "names": {"default": "Bergen busstasjon"},
                            }
                        }
                    ]
                }
            )
        )

        place = await EnturDiscoveryClient("test", session).async_get_stop_place(
            "NSR:StopPlace:548"  # type: ignore[arg-type]
        )

        self.assertEqual(place.name, "Bergen busstasjon")
        self.assertEqual(session.calls[0][1], GEOCODER_PLACE_URL)
        self.assertEqual(
            session.calls[0][2]["params"],
            {"ids": "NSR:StopPlace:548", "lang": "no"},
        )

    async def test_discovery_queries(self) -> None:
        routes_session = _Session(
            _Response(
                {
                    "data": {
                        "stopPlaces": [
                            {
                                "estimatedCalls": [
                                    {
                                        "serviceJourney": {
                                            "journeyPattern": {
                                                "line": {
                                                    "id": "BRA:Line:4_6200",
                                                    "publicCode": "4_6200",
                                                    "name": "200 Hønefoss-Oslo",
                                                    "transportMode": "bus",
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "serviceJourney": {
                                            "journeyPattern": {
                                                "line": {
                                                    "id": "BRA:Line:4_6200",
                                                    "publicCode": "4_6200",
                                                    "name": "200 Hønefoss-Oslo",
                                                    "transportMode": "bus",
                                                }
                                            }
                                        }
                                    },
                                ]
                            }
                        ]
                    }
                }
            )
        )
        routes = await EnturDiscoveryClient(
            "test", routes_session
        ).async_get_stop_routes(
            "NSR:StopPlace:548"  # type: ignore[arg-type]
        )
        self.assertEqual(
            routes,
            (EnturRoute("BRA:Line:4_6200", "4_6200", "bus", "200 Hønefoss-Oslo"),),
        )
        self.assertEqual(
            routes_session.calls[0][2]["json"],
            {
                "query": DISCOVERY_STOP_PLACE_LINES_QUERY,
                "variables": {
                    "stopPlaceId": "NSR:StopPlace:548",
                    "numberOfDepartures": 50,
                },
            },
        )

        quays_session = _Session(
            _Response(
                {
                    "data": {
                        "stopPlaces": [
                            {
                                "quays": [
                                    {
                                        "id": "NSR:Quay:1",
                                        "name": "Hønefoss sentrum",
                                        "publicCode": "A",
                                    },
                                    {
                                        "id": "NSR:Quay:1",
                                        "name": "Hønefoss sentrum",
                                        "publicCode": "A",
                                    },
                                ]
                            }
                        ]
                    }
                }
            )
        )
        quays = await EnturDiscoveryClient("test", quays_session).async_get_stop_quays(
            "NSR:StopPlace:548"  # type: ignore[arg-type]
        )
        self.assertEqual(quays, (EnturQuay("NSR:Quay:1", "Hønefoss sentrum", "A"),))
        self.assertEqual(
            quays_session.calls[0][2]["json"],
            {
                "query": DISCOVERY_STOP_PLACE_QUAYS_QUERY,
                "variables": {"stopPlaceId": "NSR:StopPlace:548"},
            },
        )

    async def test_http_and_json_errors_are_normalized(self) -> None:
        for response in (
            _Response({}, ClientResponseError(Mock(), (), status=503)),
            _Response(ValueError("bad json")),
        ):
            with self.subTest(response=response):
                client = EnturDiscoveryClient("test", _Session(response))  # type: ignore[arg-type]
                with self.assertRaises(EnturApiError):
                    await client.async_search_stop_places("Bergen")


class EnturDiscoveryParserTests(IsolatedAsyncioTestCase):
    async def test_parser_rejects_malformed_responses_and_skips_incomplete_items(
        self,
    ) -> None:
        with self.assertRaises(EnturApiError):
            _parse_stop_places({"unexpected": []})
        with self.assertRaises(EnturApiError):
            _parse_stop_routes({"errors": ["bad query"]})
        with self.assertRaises(EnturApiError):
            _parse_stop_quays({"data": {}})

        places = _parse_stop_places(
            {
                "features": [
                    None,
                    {"properties": {"id": "NSR:Quay:1"}},
                    {
                        "properties": {
                            "id": "NSR:StopPlace:1",
                            "names": "invalid",
                            "transportModes": [None, {"mode": "bus"}, {"mode": 5}],
                            "stopPlaceTypes": ["busStation", 5],
                        }
                    },
                ]
            }
        )
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0].name, "NSR:StopPlace:1")
        self.assertEqual(places[0].transport_modes, ("bus",))
        self.assertEqual(places[0].stop_place_types, ("busStation",))

    def test_route_and_quay_parsers_skip_incomplete_data_and_deduplicate(self) -> None:
        routes = _parse_stop_routes(
            {
                "data": {
                    "stopPlaces": [
                        None,
                        {},
                        {"estimatedCalls": [None, {}, {"serviceJourney": None}]},
                        {
                            "estimatedCalls": [
                                {
                                    "serviceJourney": {
                                        "journeyPattern": {
                                            "line": {
                                                "id": "RUT:Line:1",
                                                "publicCode": "1",
                                                "transportMode": "bus",
                                            }
                                        }
                                    }
                                }
                            ]
                        },
                    ]
                }
            }
        )
        quays = _parse_stop_quays(
            {
                "data": {
                    "stopPlaces": [
                        None,
                        {},
                        {"quays": [None, {}, {"id": "NSR:Quay:1", "name": 3}]},
                        {
                            "quays": [
                                {"id": "NSR:Quay:1", "name": "Platform 1"},
                                {"id": "NSR:Quay:1", "name": "Platform 1"},
                            ]
                        },
                    ]
                }
            }
        )
        self.assertEqual(routes, (EnturRoute("RUT:Line:1", "1", "bus"),))
        self.assertEqual(quays, (EnturQuay("NSR:Quay:1", "Platform 1", None),))

    def test_display_properties_handle_missing_codes_and_types(self) -> None:
        route = EnturRoute("unknown", "", "bus", "")
        place = EnturStopPlace(
            "NSR:StopPlace:1",
            "Stop",
            "Stop",
            "Stop",
            (),
            "standalone",
            ("unknown", "unknown"),
        )
        self.assertEqual(route.operator_code, "")
        self.assertEqual(route.technical_id, "unknown")
        self.assertEqual(route.selection_label, "unknown")
        self.assertEqual(
            EnturQuay("NSR:Quay:1", "Platform 1", None).selection_label, "Platform 1"
        )
        self.assertEqual(place.selection_label, "Stop")
        self.assertEqual(place.type_icons, "🚉")
