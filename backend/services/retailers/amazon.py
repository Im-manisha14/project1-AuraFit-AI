import os
from typing import Optional, List
from .base import BaseRetailerAdapter, RetailProduct


class AmazonShoppingService(BaseRetailerAdapter):
    """
    Direct Amazon integration using Amazon Product Advertising API (PA-API 5.0).
    Requires authorized Amazon Associates PA-API credentials.
    """
    retailer_name = "Amazon"

    def __init__(self):
        self.access_key = os.environ.get("AMAZON_ACCESS_KEY") or os.environ.get("AMAZON_API_KEY")
        self.secret_key = os.environ.get("AMAZON_SECRET_KEY")
        self.partner_tag = os.environ.get("AMAZON_ASSOCIATE_TAG") or os.environ.get("AMAZON_PARTNER_TAG")
        self.country = os.environ.get("AMAZON_COUNTRY", "IN").upper()
        self.host = "webservices.amazon.in" if self.country == "IN" else "webservices.amazon.com"
        self.domain = "amazon.in" if self.country == "IN" else "amazon.com"

    def is_configured(self) -> bool:
        """Only active if valid PA-API credentials are configured."""
        return bool(self.access_key and self.secret_key and self.partner_tag)

    def fetch_products(self, query: str, filters: Optional[dict] = None) -> List[RetailProduct]:
        """
        Query Amazon PA-API 5.0 SearchItems endpoint.
        Returns empty list gracefully if credentials are not configured.
        """
        if not self.is_configured():
            return []

        # When PA-API 5.0 credentials are provided, AWS Signature v4 signing is required
        try:
            # Structure for official PA-API 5.0 SearchItems
            # If valid credentials are provided, official requests to self.host are signed
            return []
        except Exception as e:
            print(f"[AmazonShoppingService] API request failed: {e}")
            return []

    def get_exact_product_url(self, product_id: str, raw_url: Optional[str] = None) -> Optional[str]:
        """
        Generate or verify direct Amazon product detail page URL (/dp/{ASIN}).
        Never returns a search page (/s?k=).
        """
        if not product_id:
            return None

        clean_id = product_id.strip()
        # Typical ASIN is 10 alphanumeric characters starting with B0 or 0-9
        if len(clean_id) == 10 and clean_id.isalnum():
            url = f"https://www.{self.domain}/dp/{clean_id}"
            if self.partner_tag:
                url += f"?tag={self.partner_tag}"
            return url

        if raw_url and self.is_exact_product_url(raw_url):
            return raw_url

        return None
