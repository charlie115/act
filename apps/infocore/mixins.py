import json
import requests

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image


class AssetMixin(object):
    def pull_asset_info(self, symbol):
        """Get asset information from CoinMarketCap

        Arguments:
            symbol -- Asset symbol (BTC, ETH, DOGE, etc.)

        Returns:
            A dictionary of asset information
        """

        data = {}

        try:
            response = requests.get(
                url=settings.COINMARKETCAP_CRYPTO_INFO_API,
                headers={"X-CMC_PRO_API_KEY": settings.COINMARKETCAP_API_KEY},
                params={"symbol": symbol},
            )

            content = json.loads(response.content)
            data = content["data"][symbol][0]

        except Exception as err:
            print(str(err))  # FIXME: Change to logging

        return data

    def get_icon_image(self, info):
        """Get asset's icon image

        Arguments:
            info -- Asset info in dictionary

        Returns:
            Asset's icon image already in django ImageField format
        """

        icon = None

        try:
            logo = Image.open(requests.get(info["logo"], stream=True).raw)
            thumb_io = BytesIO()
            logo.save(thumb_io, logo.format)

            icon = InMemoryUploadedFile(
                file=thumb_io,
                field_name=None,
                name=f"{info['symbol']}.{logo.format}",
                content_type=logo.format,
                size=logo.tell(),
                charset=None,
            )

        except Exception as err:
            print(str(err))  # FIXME: Change to logging

        return icon
