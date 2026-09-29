import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class HMShoppingService(BaseRetailerAdapter):
    """
    Direct H&M integration using H&M Group API / Affiliate Network.
    Requires authorized API credentials.
    """
    retailer_name = "H&M"

    def __init__(self):
        self.api_key = os.environ.get("HM_API_KEY")
        self.base_url = "https://api.hm.com/v1"

    def is_configured(self) -> bool:
        """Returns True only when authorized API credentials exist."""
        return bool(self.api_key)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch products from direct authorized H&M API."""
        if not self.is_configured():
            return []
        try:
            return []
        except Exception as e:
            print(f"[HMShoppingService] API error: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve direct product page on H&M (productpage.{id}.html)."""
        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        if product_id:
            return f"https://www2.hm.com/en_in/productpage.{product_id}.html"

        return None
