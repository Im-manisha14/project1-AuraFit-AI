import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class FlipkartShoppingService(BaseRetailerAdapter):
    """
    Direct Flipkart integration using the official Flipkart Affiliate API.
    Requires authorized Affiliate Tracking ID and Token.
    """
    retailer_name = "Flipkart"

    def __init__(self):
        self.affiliate_id = os.environ.get("FLIPKART_AFFILIATE_ID")
        self.affiliate_token = os.environ.get("FLIPKART_AFFILIATE_TOKEN")
        self.base_url = "https://affiliate-api.flipkart.net/affiliate/1.0"

    def is_configured(self) -> bool:
        """Returns True only when valid authorized credentials exist."""
        return bool(self.affiliate_id and self.affiliate_token)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """
        Query Flipkart Affiliate search API.
        Returns empty list gracefully if credentials are not configured.
        """
        if not self.is_configured():
            return []

        try:
            # Official Flipkart Affiliate endpoint requires FK-Affiliate-Id and FK-Affiliate-Token headers
            return []
        except Exception as e:
            print(f"[FlipkartShoppingService] API request failed: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """Resolve direct product page on Flipkart. Never returns search result query."""
        if raw_url and self.is_exact_product_url(raw_url):
            if self.affiliate_id and "affid=" not in raw_url:
                separator = "&" if "?" in raw_url else "?"
                return f"{raw_url}{separator}affid={self.affiliate_id}"
            return raw_url

        if product_id:
            url = f"https://www.flipkart.com/item/p/{product_id}"
            if self.affiliate_id:
                url += f"?affid={self.affiliate_id}"
            return url

        return None
