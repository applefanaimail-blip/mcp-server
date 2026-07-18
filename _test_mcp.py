"""Test MCP server connection using the official MCP Python SDK."""

import asyncio
import json
import logging
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_test")

SERVER_URL = "https://bridgenode.cc/mcp/sse"


async def test_mcp():
    logger.info(f"Connecting to MCP server: {SERVER_URL}")

    async with sse_client(url=SERVER_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Initialize
            await session.initialize()
            logger.info("✅ MCP session initialized")

            # List tools
            tools = await session.list_tools()
            logger.info(f"✅ Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                logger.info(f"   - {tool.name}: {tool.description[:60]}...")

            # List resources
            resources = await session.list_resources()
            logger.info(f"✅ Resources: {len(resources.resources)}")

            # List prompts
            prompts = await session.list_prompts()
            logger.info(f"✅ Prompts: {len(prompts.prompts)}")

            logger.info("🎉 MCP server test COMPLETE")
            return True


if __name__ == "__main__":
    success = asyncio.run(test_mcp())
    sys.exit(0 if success else 1)
