from .base import RetailProduct, BaseRetailerAdapter
from .amazon import AmazonShoppingService
from .flipkart import FlipkartShoppingService
from .myntra import MyntraShoppingService
from .nykaa import NykaaShoppingService
from .ajio import AjioShoppingService
from .meesho import MeeshoShoppingService
from .hm import HMShoppingService
from .zara import ZaraShoppingService
from .registry import MultiRetailerShoppingManager

__all__ = [
    "RetailProduct",
    "BaseRetailerAdapter",
    "AmazonShoppingService",
    "FlipkartShoppingService",
    "MyntraShoppingService",
    "NykaaShoppingService",
    "AjioShoppingService",
    "MeeshoShoppingService",
    "HMShoppingService",
    "ZaraShoppingService",
    "MultiRetailerShoppingManager",
]
