"""
API Clients Module

Contains all external API clients for integrating with third-party services
"""

from .base_client import BaseAPIClient
from .open_meteo_client import OpenMeteoClient

__all__ = [
    "BaseAPIClient",
    "OpenMeteoClient",
]