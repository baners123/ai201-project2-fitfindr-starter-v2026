"""
FitFindr MCP server.

Exposes search_listings through the Model Context Protocol.
"""

from mcp.server.fastmcp import FastMCP
from tools import search_listings as _search_listings_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Search thrift listings and return matching listing dictionaries."""
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()
