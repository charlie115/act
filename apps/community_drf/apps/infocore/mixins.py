import json
import string
import logging

from django_rq import job
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image

from integrations.assets import CoinMarketCapClient
from lib.status import HTTP_200_OK


class AssetMixin(object):
    logger = logging.getLogger(__name__)

    def get_coinmarketcap_client(self):
        return CoinMarketCapClient(
            crypto_info_url=settings.COINMARKETCAP_CRYPTO_INFO_API,
            api_key=settings.COINMARKETCAP_API_KEY,
        )

    @job
    def pull_asset_info(self, symbol):
        """Get asset information from CoinMarketCap

        Arguments:
            symbol -- Asset symbol (BTC, ETH, DOGE, etc.)

        Returns:
            A dictionary of asset information
        """

        data = {}

        try:
            client = self.get_coinmarketcap_client()
            response = client.get_asset_info(symbol)
            content = json.loads(response.content)

            if response.status_code == HTTP_200_OK and "data" in content:
                data = content["data"][symbol][0]
            else:
                data["note"] = content["status"]["error_message"]

                if "Invalid value" in content["status"]["error_message"] and any(
                    char.isdigit() for char in symbol
                ):
                    cleaned_symbol = symbol.rstrip(string.digits).lstrip(string.digits)

                    response = client.get_asset_info(cleaned_symbol)
                    content = json.loads(response.content)

                    if response.status_code == HTTP_200_OK and "data" in content:
                        data = content["data"][cleaned_symbol][0]
                        data["note"] = f"Icon was pulled based on {cleaned_symbol}"

        except Exception as err:
            data["note"] = str(err)
            self.logger.exception("pull_asset_info failed for symbol=%s", symbol)
            raise err

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
            logo_response = self.get_coinmarketcap_client().fetch_logo(info["logo"])
            logo = Image.open(logo_response.raw)
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
            self.logger.exception("get_icon_image failed for symbol=%s", info.get("symbol"))

        return icon
