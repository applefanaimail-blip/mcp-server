# BridgeNode MCP Server

**DeepSeek V4 Flash inference via [Model Context Protocol](https://modelcontextprotocol.io/)**

Pay per request with Solana USDC via x402 protocol — no registration, no API keys, no KYC.

## Quick Start

Connect in 10 seconds:

### Claude Desktop

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

Settings → Cursor Settings → MCP → Add global MCP server:

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

| Parameter | Type | Required | Description |
|-----------|------|:--------:|-------------|
| `messages` | string | ✅ | JSON string of OpenAI chat messages |
| `max_tokens` | int | ❌ | Max tokens (default 256) |
| `solana_key` | string | ✅ | Base58-encoded Solana private key |

### Example

```
inference(messages='[{"role": "user", "content": "Hello, what is AI?"}]', solana_key="<your_base58_key>")
```

The server auto-generates a UUID nonce, signs it with your key, and sends the request. One parameter — done.

## Step 1 — Deposit USDC

Send USDC (Solana mainnet) to:

```
BHMDv3ri3LBEZjEzJgDZeUiguVX7LmsCstTXbM3dL8rN
```

**Asset:** `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` (USDC)

Check your balance:

```
https://bridgenode.cc/v1/balance/{your_wallet_address}
```

## Step 2 — Call inference

Use any MCP client. **Auto-auth** via `solana_key`:

```
inference(messages='[{"role": "user", "content": "Hello"}]', solana_key="<your_base58_key>")
```

Cost: ~$0.001–0.005 per request (dynamic, based on token usage).

## Endpoint

| Transport | URL |
|-----------|-----|
| SSE | `https://bridgenode.cc/mcp/sse` |
| Messages | `https://bridgenode.cc/mcp/messages/` |

## How it works

1. Agent connects to `bridgenode.cc/mcp/sse` via standard MCP SSE transport
2. Calls `inference()` with messages + solana_key
3. MCP server decodes the key, generates a UUID nonce, creates an ed25519 signature
4. Sends `POST /v1/inference` to BridgeNode with `X-Address`, `X-Nonce`, `X-Signature` headers
5. BridgeNode verifies the signature, checks balance, proxies to DeepSeek
6. Response returned to the agent

## Links

- [BridgeNode](https://bridgenode.cc)
- [x402 Protocol](https://x402.org)
- [MCP Specification](https://modelcontextprotocol.io)

## License

MIT
