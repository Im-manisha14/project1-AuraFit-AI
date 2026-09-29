import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class NykaaShoppingService(BaseRetailerAdapter):
    """
    Direct Nykaa Fashion integration using Nykaa Affiliate/Partner API.
    Requires authorized partner credentials.
    """
    retailer_name = "Nykaa"

    def __init__(self):
        self.api_key = os.environ.get("NYKAA_API_KEY")
        self.client_id = os.environ.get("NYKAA_CLIENT_ID")
        self.base_url = "https://api.nykaa.com/v1"

    def is_configured(self) -> bool:
        """Returns True only when authorized credentials exist."""
        return bool(self.api_key and self.client_id)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch products from direct authorized Nykaa API."""
        if not self.is_configured():
            return []
        try:
            return []
        except Exception as e:
            print(f"[NykaaShoppingService] API error: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve direct product page on Nykaa Fashion."""
        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        if product_id:
            return f"https://www.nykaafashion.com/p/p/{product_id}"

        return None
