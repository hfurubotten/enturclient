# Entur API client

Python client for fetching estimated departures from stop places in Norway from Entur.org's API. Information about stop places, platforms and real-time departures.

[![PyPI version fury.io][pypi-version-badge]][pypi-enturclient]
[![PyPI pyversions][py-versions-badge]][pypi-enturclient]

[![Buy me a coffee][buymeacoffee-shield]][buymeacoffee]

## Usage

```python
import aiohttp
import asyncio
from enturclient import EnturPublicTransportData

API_CLIENT_ID = 'awesome_company-my_application' 
        
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
    
loop = asyncio.get_event_loop()
loop.run_until_complete(print_bergen_train_delay())
```

## Obtaining a stop id
 [Entur's travel planer](https://en-tur.no) has a map of all stops used in Norway. Use the map to find the stops you're interested in. When you have found one of your stops, click on it. 
 Now the web browser should contain an URL with the id in it. Such as this: 
 `https://en-tur.no/nearby-stop-place-detail?id=NSR:StopPlace:32376`
 The stop id is the content after id= parameter in the url. Copy paste this into the configuration. 

[buymeacoffee-shield]: https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg
[buymeacoffee]: https://www.buymeacoffee.com/heine
[pypi-enturclient]: https://pypi.org/project/enturclient/
[pypi-version-badge]: https://badge.fury.io/py/enturclient.svg
[py-versions-badge]: https://img.shields.io/pypi/pyversions/enturclient.svg
