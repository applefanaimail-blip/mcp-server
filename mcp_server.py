"""MCP (Model Context Protocol) server for BridgeNode.

Exposes inference as an MCP tool via SSE transport.
Mount on existing FastAPI app: app.mount("/mcp/", create_sse_server(mcp))

Auth: provide your Solana private key (base58) as solana_key.
The server generates a nonce, signs it, and sends auth headers automatically.
"""

import base64
import json
import logging
import time
import uuid

import base58
import httpx
import nacl.signing
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from config import BASE_URL

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("BridgeNode")


def _derive_keypair(base58_key: str) -> tuple:
    """Decode a base58 Solana keypair and return (signing_key, address).

    Accepts either a 64-byte keypair (seed || public_key) or a 32-byte seed.
    Returns a nacl SigningKey and base58-encoded Solana address.
    """
    decoded = base58.b58decode(base58_key)

    if len(decoded) == 64:
        seed = decoded[:32]
    elif len(decoded) == 32:
        seed = decoded
    else:
        raise ValueError(
            f"Invalid key length: {len(decoded)} bytes (expected 32 or 64)"
        )

    signing_key = nacl.signing.SigningKey(seed)
    verify_key = signing_key.verify_key
    address = base58.b58encode(bytes(verify_key)).decode()
    return signing_key, address


def _auto_sign(base58_key: str) -> tuple:
    """Generate nonce and sign it with the given key.

    Returns (x_address, x_nonce, x_signature).
    """
    signing_key, address = _derive_keypair(base58_key)
    nonce = str(uuid.uuid4())
    sig_bytes = signing_key.sign(nonce.encode()).signature
    sig_b64 = base64.b64encode(sig_bytes).decode()
    return address, nonce, sig_b64


@mcp.tool()
async def inference(
    messages: str,
    max_tokens: int = 256,
    solana_key: str = "",
) -> str:
    """DeepSeek V4 Flash inference via BridgeNode.

    Sends a chat completion request to DeepSeek V4 Flash.
    Pre-deposit USDC to BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN (Solana mainnet).

    Auth: provide your Solana private key (base58) as solana_key.
    The server auto-generates a UUID nonce and signs it — no manual signing needed.

    Args:
        messages: JSON string of messages array, e.g. [{"role": "user", "content": "Hello"}]
        max_tokens: Maximum tokens in the response (default 256)
        solana_key: Base58-encoded Solana private key for auth (required)

    Returns:
        The assistant's response text
    """
    if not solana_key:
        return (
            "Error: 'solana_key' is required. "
            "Provide your base58-encoded Solana private key as solana_key."
        )

    try:
        x_address, x_nonce, x_signature = _auto_sign(solana_key)
    except Exception as e:
        return f"Error: failed to sign with solana_key: {e}"

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
            cost_str = ""
            try:
                body = resp.json()
                required = body.get("required", {})
                if required:
                    cost_str = f" Requires {required.get('amount', '?')} {required.get('asset', 'USDC')}."
            except Exception:
                pass
            return (
                f"Payment required.{cost_str} "
                f"Pre-deposit USDC to BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN. "
                f"Balance check at {BASE_URL}/v1/balance/{x_address}"
            )

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

        logger.info(
            f"MCP inference addr={x_address[:12]}... "
            f"tokens={meta.get('token_stats', {})} "
            f"cost=${meta.get('cost_usd', 0):.6f} "
            f"time={elapsed:.2f}s"
        )

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
