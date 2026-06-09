# pvemcp installation and MCP wiring

## Native plugin layout (Codex)

`pvemcp` now includes native plugin metadata and skill packaging:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `plugin/scripts/start-pvemcp.sh`
- `plugin/skills/pvemcp/SKILL.md`

This means Codex can consume pvemcp as a first-class MCP+skill plugin without custom per-tool scaffolding.

## Install from git (host-side)

```bash
python -m pip install git+https://github.com/SWORDIntel/pvemcp.git
```

## Editable install for local development

```bash
git clone https://github.com/SWORDIntel/pvemcp.git
cd pvemcp
python -m pip install -e .
```

## MCP entrypoint

```bash
pvemcp-server
```

This launches the MCP server using stdio transport via `FastMCP("PveMCP")`.

## Client wiring (Codex / Gemini style)

- Copied samples:
  - `examples/codex-mcp.json`
  - `examples/gemini-mcp.json`
- Replace only paths/values and merge into your client config.

```json
{
  "mcpServers": {
    "pvemcp": {
      "command": "pvemcp-server",
      "env": {
        "PVEMCP_AUDIT_LOG": "/var/log/pvemcp-audit.log",
        "PVEMCP_ALLOW_BREAK_GLASS": "1"
      }
    }
  }
}
```

## Host trust behavior

- Host commands are allowed to run without strict checks automatically when:
  - `PVEMCP_ALLOW_BREAK_GLASS=1`
  - or `/etc/pve` exists (i.e., when running on a Proxmox host).

For everything else, guest actions continue to be policy-constrained.

## One-shot install helper

```bash
chmod +x scripts/install-pvemcp.sh
scripts/install-pvemcp.sh --client both
```

Install client configs, register Codex natively, and optionally start the service in one pass:

```bash
scripts/install-pvemcp.sh --client both --install-service
```

The installer now also updates:

```text
~/.codex/settings.json
```

by merging `mcpServers.pvemcp` under the `mcpServers` section when `--client codex` or `--client both` is used.

### Uninstall

Remove local file artifacts and native Codex registration from the unified installer:

```bash
scripts/install-pvemcp.sh --uninstall
```

To also remove the systemd unit:

```bash
scripts/install-pvemcp.sh --uninstall --remove-service
```

Default client configs are written under:

```text
~/.codex/mcp/pvemcp-*.json
```

## Optional: run as a systemd service

Use this unit file when you want `pvemcp-server` to start automatically on the host.

```bash
sudo cp examples/pvemcp.service /etc/systemd/system/pvemcp.service
sudo systemctl daemon-reload
sudo systemctl enable --now pvemcp.service
sudo systemctl status pvemcp.service
```

If you need to tune env values, edit `/etc/systemd/system/pvemcp.service` before reloading.
