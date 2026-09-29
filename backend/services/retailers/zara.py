import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class ZaraShoppingService(BaseRetailerAdapter):
    """
    Direct Zara / Inditex integration using Inditex Developer API.
    Requires authorized partner credentials.
    """
    retailer_name = "Zara"

    def __init__(self):
        self.api_key = os.environ.get("ZARA_API_KEY")
        self.base_url = "https://api.zara.com/v1"

    def is_configured(self) -> bool:
        """Returns True only when authorized API credentials exist."""
        return bool(self.api_key)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch products from direct authorized Zara API."""
        if not self.is_configured():
            return []
        try:
            return []
        except Exception as e:
            print(f"[ZaraShoppingService] API error: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve direct product page on Zara."""
        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        if product_id:
            return f"https://www.zara.com/in/en/{product_id}-p.html"

        return None
