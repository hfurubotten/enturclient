# Entur API client

Python client for fetching estimated departures from stop places in Norway from [`entur.org`](https://developer.entur.org) API. Information about stop places, platforms and real-time departures.

[![PyPI version fury.io][pypi-version-badge]][pypi-enturclient]
[![PyPI pyversions][py-versions-badge]][pypi-enturclient]

[![Buy me a coffee][buymeacoffee-shield]][buymeacoffee]

## Usage

```python
import aiohttp
import asyncio
from enturclient import EnturPublicTransportData

API_CLIENT_ID = 'awesome_company - my_application'

async def print_bergen_train_delay():
    async with aiohttp.ClientSession() as client:
        stops = ['NSR:StopPlace:548']
        quays = ['NSR:Quay:48550']

        data = EnturPublicTransportData(
            client_name=API_CLIENT_ID, # Required
            stops=stops,
            quays=quays,
            omit_non_boarding=True,
            number_of_departures=5,
            web_session=client) # recommended argument

        await data.update()

        bergen_train = data.get_stop_info('NSR:StopPlace:548')
        bergen_train_delay = bergen_train.estimated_calls[0].delay_in_min

        print(bergen_train_delay)

asyncio.run(print_bergen_train_delay())
```

## Obtaining a stop id

[Entur's travel planer](https://en-tur.no) has a map of all stops used in Norway. Use the map to find the stops you're interested in. When you have found one of your stops, click on it, and hit "Se alle avganger".

Now the web browser should contain an URL with the id in it. Such as this:
`https://en-tur.no/nearby-stop-place-detail?id=NSR:StopPlace:32376`

The stop id is the content after `id=` parameter in the url. Copy paste this into the configuration.

It's also possible to use the National Stop Register (NSR).
Log in as "guest"/"guest" at https://stoppested.entur.org to explore the contents of NSR.
Find your stop in the map, click on it and then again at the name. You have to zoom quite a bit in before the stops shows in the map. Information about the stop place, including the stop and quay ids will pop up on the side.

[buymeacoffee-shield]: https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg
[buymeacoffee]: https://www.buymeacoffee.com/heine
[pypi-enturclient]: https://pypi.org/project/enturclient/
[pypi-version-badge]: https://badge.fury.io/py/enturclient.svg
[py-versions-badge]: https://img.shields.io/pypi/pyversions/enturclient.svg
