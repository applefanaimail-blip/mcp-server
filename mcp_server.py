"""MCP (Model Context Protocol) server for BridgeNode.

Exposes inference as an MCP tool via SSE transport.
Mount on existing FastAPI app: app.mount("/mcp/", create_sse_server(mcp))
"""

import json
import logging
import time

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from config import BASE_URL

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("BridgeNode")


@mcp.tool()
async def inference(
    messages: str,
    max_tokens: int = 256,
    x_address: str = "",
    x_nonce: str = "",
    x_signature: str = "",
) -> str:
    """DeepSeek V4 Flash inference via BridgeNode.

    Sends a chat completion request to DeepSeek V4 Flash.
    Pre-deposit USDC to BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN (Solana mainnet).

    Auth: generate a UUID nonce, sign it with your Solana private key (ed25519),
    and provide X-Address (your Solana wallet), X-Nonce (the UUID), X-Signature (the base64 signature).

    Args:
        messages: JSON string of messages array, e.g. [{"role": "user", "content": "Hello"}]
        max_tokens: Maximum tokens in the response (default 256)
        x_address: Solana wallet address for auth
        x_nonce: UUID nonce for signature verification
        x_signature: Base64-encoded ed25519 signature of the nonce

    Returns:
        The assistant's response text
    """
    if not all([x_address, x_nonce, x_signature]):
        return "Error: Missing authentication headers. Provide X-Address, X-Nonce, and X-Signature."

    try:
        parsed_messages = json.loads(messages)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in messages parameter: {e}"

    t0 = time.perf_counter()

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{BASE_URL}/v1/inference",
            json={
                "messages": parsed_messages,
                "max_tokens": max_tokens,
                "stream": False,
                "model": "deepseek-v4-flash",
            },
            headers={
                "X-Address": x_address,
                "X-Nonce": x_nonce,
                "X-Signature": x_signature,
                "Content-Type": "application/json",
            },
        )

        elapsed = time.perf_counter() - t0

        if resp.status_code == 402:
            return f"Payment required. Pre-deposit USDC to BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN. Balance check at {BASE_URL}/v1/balance/{x_address}"

        if resp.status_code != 200:
            body = resp.text[:500]
            logger.warning(f"MCP inference failed (HTTP {resp.status_code}): {body}")
            return f"Error: HTTP {resp.status_code} — {body}"

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return "No response generated."

        text = choices[0].get("message", {}).get("content", "")
        meta = data.get("response_metadata", {})

        logger.info(f"MCP inference addr={x_address[:12]}... tokens={meta.get('token_stats', {})} cost=${meta.get('cost_usd', 0):.6f} time={elapsed:.2f}s")

        return text.strip()


def create_sse_server(mcp_instance: FastMCP = None) -> Starlette:
    """Create a Starlette app that handles MCP SSE connections."""
    if mcp_instance is None:
        mcp_instance = mcp

    transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_instance._mcp_server.run(
                streams[0],
                streams[1],
                mcp_instance._mcp_server.create_initialization_options(),
            )

    routes = [
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=transport.handle_post_message),
    ]

    return Starlette(routes=routes)
