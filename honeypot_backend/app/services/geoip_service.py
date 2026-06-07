import geoip2.database
from geoip2.errors import AddressNotFoundError
import functools
import ipaddress
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class GeoIPResult(BaseModel):
    country: str = "Unknown"
    country_code: str = "UNK"
    city: str = "Unknown"
    lat: float | None = None
    lon: float | None = None
    asn: str = "Unknown"

class GeoIPService:
    def __init__(self):
        self.settings = get_settings()
        self.city_reader = None
        self.asn_reader = None

    def startup(self):
        try:
            self.city_reader = geoip2.database.Reader(self.settings.GEOIP_CITY_DB)
            self.asn_reader = geoip2.database.Reader(self.settings.GEOIP_ASN_DB)
            logger.info("GeoIP databases loaded successfully")
        except FileNotFoundError as e:
            logger.warning(f"GeoIP database not found, enrichment will be limited: {e}")
        except Exception as e:
            logger.error(f"Failed to load GeoIP database: {e}")

    def close(self):
        if self.city_reader:
            self.city_reader.close()
        if self.asn_reader:
            self.asn_reader.close()

    @functools.lru_cache(maxsize=10000)
    def enrich(self, ip: str) -> GeoIPResult:
        result = GeoIPResult()

        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                result.country = "Private"
                result.country_code = "PRV"
                result.city = "Private"
                return result
        except ValueError:
            result.country = "Invalid"
            result.country_code = "INV"
            return result

        if self.city_reader:
            try:
                city_response = self.city_reader.city(ip)
                result.country = city_response.country.name or "Unknown"
                result.country_code = city_response.country.iso_code or "UNK"
                result.city = city_response.city.name or "Unknown"
                result.lat = city_response.location.latitude
                result.lon = city_response.location.longitude
            except AddressNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Error reading city database for {ip}: {e}")

        if self.asn_reader:
            try:
                asn_response = self.asn_reader.asn(ip)
                result.asn = asn_response.autonomous_system_organization or "Unknown"
            except AddressNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Error reading asn database for {ip}: {e}")

        return result

geoip_service = GeoIPService()
