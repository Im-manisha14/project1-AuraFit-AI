from typing import Dict, List, Optional, Any
from .base import BaseRetailerAdapter, RetailProduct
from .amazon import AmazonShoppingService
from .flipkart import FlipkartShoppingService
from .myntra import MyntraShoppingService
from .nykaa import NykaaShoppingService
from .ajio import AjioShoppingService
from .meesho import MeeshoShoppingService
from .hm import HMShoppingService
from .zara import ZaraShoppingService


class MultiRetailerShoppingManager:
    """
    Orchestrates retailer adapters and multi-retailer discovery with strict priority:
      1. Direct authorized retailer API (activated only when credentials present)
      2. Exact retailer offer URL obtained through supported shopping integration
      3. SerpApi product/offer information with resolved exact seller URL
      4. If no exact purchasable URL exists, mark the product as non-purchasable
    """

    def __init__(self):
        self.adapters: Dict[str, BaseRetailerAdapter] = {
            "Amazon": AmazonShoppingService(),
            "Flipkart": FlipkartShoppingService(),
            "Myntra": MyntraShoppingService(),
            "Nykaa": NykaaShoppingService(),
            "AJIO": AjioShoppingService(),
            "Meesho": MeeshoShoppingService(),
            "H&M": HMShoppingService(),
            "Zara": ZaraShoppingService(),
        }

    def get_adapter(self, retailer_name: str) -> Optional[BaseRetailerAdapter]:
        """Look up adapter by normalized retailer name."""
        name_clean = (retailer_name or "").strip().lower()
        for key, adapter in self.adapters.items():
            if key.lower() == name_clean or key.lower() in name_clean:
                return adapter
        return None

    def get_configured_adapters(self) -> List[BaseRetailerAdapter]:
        """Return list of adapters with verified authorized credentials."""
        return [adapter for adapter in self.adapters.values() if adapter.is_configured()]

    def get_retailer_status_matrix(self, serpapi_configured: bool = False) -> List[Dict[str, Any]]:
        """
        Produce real-time verification matrix of retailer support across all integration layers.
        """
        from models.outfit import Outfit

        matrix = []
        for name, adapter in self.adapters.items():
            direct_api = adapter.is_configured()

            # Check if database has products for this retailer with verified exact product URL & in_stock
            store_match = Outfit.query.filter(
                (Outfit.store.ilike(f"%{name}%")) | (Outfit.brand.ilike(f"%{name}%"))
            ).all()

            has_exact_url = any(Outfit.is_exact_product_url(o.product_url) for o in store_match)
            has_purchasable = any(
                Outfit.is_exact_product_url(o.product_url) and o.in_stock and o.purchasable
                for o in store_match
            )

            matrix.append({
                "retailer": name,
                "direct_api_access": direct_api,
                "serpapi_access": serpapi_configured,
                "exact_product_url_available": has_exact_url,
                "purchasable_product_available": has_purchasable,
                "total_catalog_products": len(store_match)
            })

        return matrix
