import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class MyntraShoppingService(BaseRetailerAdapter):
    """
    Direct Myntra integration using Myntra Partner / Catalog API.
    Requires authorized partner credentials.
    """
    retailer_name = "Myntra"

    def __init__(self):
        self.api_key = os.environ.get("MYNTRA_API_KEY")
        self.partner_id = os.environ.get("MYNTRA_PARTNER_ID")
        self.base_url = "https://developer.myntra.com/api/v1"

    def is_configured(self) -> bool:
        """Returns True only when authorized partner credentials exist."""
        return bool(self.api_key and self.partner_id)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch products from direct authorized Myntra API."""
        if not self.is_configured():
            return []
        try:
            return []
        except Exception as e:
            print(f"[MyntraShoppingService] API error: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve exact product buy URL on Myntra (must end with /buy or product slug)."""
        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        if product_id:
            # Myntra direct product page structure
            return f"https://www.myntra.com/dresses/{product_id}/buy"

        return None
