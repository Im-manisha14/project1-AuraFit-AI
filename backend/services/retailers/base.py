import re
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class RetailProduct:
    """
    Standardized commercial product interface across all retailers and discovery layers.
    """
    external_id: str
    title: str
    retailer: str
    brand: Optional[str]
    price: float
    currency: str
    original_price: Optional[float]
    image_url: str
    product_url: str
    availability: str
    source: str
    purchasable: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseRetailerAdapter(ABC):
    """
    Base class for authorized direct retailer API integrations.
    Only active when official authorized credentials exist in the environment.
    """
    retailer_name: str = "Unknown"

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True only when valid authorized API credentials exist in environment."""
        pass

    @abstractmethod
    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch live products directly from authorized retailer API."""
        pass

    @abstractmethod
    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve the verified, direct retailer product detail page URL."""
        pass

    @staticmethod
    def is_exact_product_url(url: Optional[str]) -> bool:
        """
        Verify that a URL is a genuine direct product page and NOT a search results page.
        Never allows /s?k=, /search?q=, or placeholder domains.
        """
        if not url or not isinstance(url, str):
            return False
        url_clean = url.strip()
        if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
            return False

        url_lower = url_clean.lower()
        # Reject placeholder and internal test domains
        if any(d in url_lower for d in ['aurafit.store', 'example.com', 'placeholder', 'localhost', '127.0.0.1']):
            return False

        # Reject search query patterns
        search_patterns = [
            'amazon.in/s?', 'amazon.com/s?', 'amazon.in/s/', 'amazon.com/s/',
            '/search?', '/search/', 'rawquery=', '?q=', '&q=', 'searchterm=',
            'google.com/search', 'google.com/shopping', 'google.com/url?'
        ]
        if any(sp in url_lower for sp in search_patterns):
            return False

        return True

    @staticmethod
    def unwrap_redirect_url(url: Optional[str]) -> Optional[str]:
        """Unwrap Google or affiliate wrapper redirects if target is present in query string."""
        if not url:
            return None
        if 'google.com/url?' in url:
            try:
                parsed = urllib.parse.urlparse(url)
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get('url', [None])[0] or qs.get('q', [None])[0]
                if target:
                    return urllib.parse.unquote(target).strip()
            except Exception:
                pass
        return url
