# BridgeNode MCP Server

DeepSeek V4 Flash inference via [Model Context Protocol](https://modelcontextprotocol.io/). Pay per request with Solana USDC via x402 protocol — no registration, no API keys, no KYC.

## Endpoint

| Transport | URL |
|-----------|-----|
| SSE | `https://bridgenode.cc/mcp/sse` |
| Messages | `https://bridgenode.cc/mcp/messages/` |

## Quick Start

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bridgenode": {
      "url": "https://bridgenode.cc/mcp/sse"
    }
  }
}
```

### Cursor

Settings → Cursor Settings → MCP → Add new global MCP server:

```json
{
  "mcpServers": {
    "bridgenode": {
      "url": "https://bridgenode.cc/mcp/sse"
    }
  }
}
```

### Claude Code CLI

```bash
claude mcp add --transport http "bridgenode" "https://bridgenode.cc/mcp/sse"
```

### OpenClaw

```bash
openclaw mcp add --url https://bridgenode.cc/mcp/sse
```

## Usage

Call the `inference` tool with:

- `messages` — JSON string of OpenAI chat messages
- `max_tokens` — (optional, default 256)
- `x_address` — your Solana wallet address
- `x_nonce` — UUID v4 for signature
- `x_signature` — base64 ed25519 signature of the nonce (sign with your Solana private key)

### Authentication

1. Generate a UUID v4 nonce
2. Sign the nonce bytes with your Solana wallet's ed25519 private key
3. Base64-encode the signature
4. Send `x_address`, `x_nonce`, `x_signature` as tool arguments

### Payment

Pre-deposit USDC to: `BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN` (Solana mainnet)

Check balance: `https://bridgenode.cc/v1/balance/{your_address}`

Cost: ~$0.001–0.005 per request (dynamic, based on token usage)

## Links

- [BridgeNode](https://bridgenode.cc)
- [x402 Protocol](https://x402.org)
- [MCP Specification](https://modelcontextprotocol.io)

## License

MIT
