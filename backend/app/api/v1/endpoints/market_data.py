"""
Market data API endpoints for the central server.

This is the main market data router that includes endpoints
from all modularized components organized in the market_data package.
"""

# Import the combined router from the market_data package
from .market_data import router
