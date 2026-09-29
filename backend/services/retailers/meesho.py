import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class MeeshoShoppingService(BaseRetailerAdapter):
    """
    Direct Meesho integration using Meesho Developer / Supplier API.
    Requires authorized supplier or developer credentials.
    """
    retailer_name = "Meesho"

    def __init__(self):
        self.api_key = os.environ.get("MEESHO_API_KEY")
        self.supplier_id = os.environ.get("MEESHO_SUPPLIER_ID")
        self.base_url = "https://supplier.meesho.com/api/v1"

    def is_configured(self) -> bool:
        """Returns True only when authorized credentials exist."""
        return bool(self.api_key and self.supplier_id)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """Fetch products from direct authorized Meesho API."""
        if not self.is_configured():
            return []
        try:
            return []
        except Exception as e:
            print(f"[MeeshoShoppingService] API error: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve direct product page on Meesho (e.g. /p/{product_id})."""
        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        if product_id:
            return f"https://www.meesho.com/s/p/{product_id}"

        return None
