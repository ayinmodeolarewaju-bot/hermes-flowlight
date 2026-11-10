"""Flowlight — live on-chain money flows for Hermes Agent."""

from __future__ import annotations

import logging
from pathlib import Path

from .cli import handle_cli, setup_cli, slash_command
from .schemas import TOOL_SCHEMAS
from .tools import HANDLERS, bind_context

PLUGIN_ID = "flowlight"
logger = logging.getLogger(__name__)


def register(ctx) -> None:
    """Register tools, /flowlight, the CLI, and the bundled skill."""
    bind_context(ctx)
    for name, schema in TOOL_SCHEMAS.items():
        ctx.register_tool(
            name=name,
            toolset="flowlight",
            schema=schema,
            handler=HANDLERS[name],
        )
    skills_dir = Path(__file__).resolve().parent / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.is_file():
                ctx.register_skill(child.name, skill_md)
    ctx.register_command(
        "flowlight",
        slash_command,
        description="Watch public wallets and narrate on-chain flows (read-only)",
        args_hint="[watch|flows|summary|list|invoices|demo] ...",
    )
    ctx.register_cli_command(
        name="flowlight",
        help="Watch wallets and open the flow picture",
        description="Read-only on-chain money flows. Never signs or sends transactions.",
        setup_fn=setup_cli,
        handler_fn=handle_cli,
    )
    logger.debug("flowlight registered %d tools", len(TOOL_SCHEMAS))
