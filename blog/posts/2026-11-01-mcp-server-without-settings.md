---
title: "Giving coding agents an MCP server without writing to their settings"
slug: mcp-server-without-settings
date: 2026-11-01
description: "Yardlet hands Codex, Claude Code and ACP agents its MCP server one session at a time: a launch argument for one, a request field for the others. Nothing is written to their settings."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents like Codex and Claude Code in one window. The agents get a few tools from it: a browser panel they can drive while I watch, a view of my other tasks, and the connectors I signed in to once. All of that comes through one small MCP server in the app bundle, `yardlet-mcp`.

The usual way to give an agent an MCP server is to register it in the agent's settings: `claude mcp add` for Claude Code, an `mcp_servers` entry in `config.toml` for Codex. Yardlet doesn't. It passes the server to each session as it starts, through whatever that agent accepts for one session. This post is about why, and what each agent accepts.

## Why not the settings file

Early on I considered things that would have made Yardlet matter more to the agent: a hook that handles approvals, performance numbers sent with every turn. I dropped them. Yardlet runs each agent's own CLI, and what it changes for a session, it changes in that process only, with an argument or an environment variable. I wanted two things to hold:

- What Yardlet adds, you can switch off in its settings, and the agent's own files don't change either way.
- Quit Yardlet or drag it to the Trash, and the agents, their sign-ins and their sessions are as they were.

A server in the agent's settings would break the second one. Every session, in Yardlet or not, would start the server. With Yardlet closed, it would still list its browser tools and answer every call with an error. Remove the app, and the entry stays, pointing at a command that is gone.

## What each agent accepts for one session

**Claude Code** takes `--mcp-config <file>`. Yardlet writes one file per session, with the server and the session's token in its environment:

```json claude-<session>.json
{
  "mcpServers": {
    "yardlet": {
      "type": "stdio",
      "command": "/Applications/Yardlet.app/Contents/Helpers/yardlet-mcp",
      "args": [],
      "env": {
        "YARDLET_TOOLS_SOCKET": "…/tools.sock",
        "YARDLET_TOOLS_TOKEN": "…",
        "YARDLET_TOOLS_SESSION": "…",
        "YARDLET_TOOLS_APP_PID": "…"
      }
    }
  }
}
```

A JSON argument would work too, but then the token would show in the process list. So the file sits in a folder only the user can open, under the temporary directory of that run of Yardlet. It goes when Yardlet quits; a run that crashed leaves it, and the next run removes it. The argument goes last, because it takes several values, so nothing after it is taken as one of them. I don't pass `--strict-mcp-config`, which would drop the servers you registered yourself. They load beside Yardlet's, with one exception: when a Yardlet connector is connected for the same address as one of your Claude servers, that server is denied for this process through `--settings`, so the agent isn't offered the same service twice. That is a launch argument too.

**Codex** runs as an App Server, and `thread/start`, `thread/resume` and `thread/fork` take a `config` object for that thread:

```json config in thread/start
{
  "mcp_servers": {
    "yardlet": {
      "command": "/Applications/Yardlet.app/Contents/Helpers/yardlet-mcp",
      "args": [],
      "env": {
        "YARDLET_TOOLS_SOCKET": "…/tools.sock",
        "YARDLET_TOOLS_TOKEN": "…",
        "YARDLET_TOOLS_SESSION": "…",
        "YARDLET_TOOLS_APP_PID": "…"
      },
      "tool_timeout_sec": 1800
    }
  }
}
```

Codex merges it over the user's configuration. I checked with a server of my own in the `config.toml` of a temporary home: `mcpServerStatus/list` showed both connected. The timeout is there because a browser call can wait for a page to load, longer than Codex's default.

**ACP agents** (OpenCode, Kimi Code, Grok Build, Hermes) take `mcpServers` in `session/new` and `session/load`. The protocol makes stdio servers mandatory for them. OpenCode, in a temporary home, started the server from that field and asked it for the tool list.

**Cursor Agent, Antigravity CLI, Pi and Muse Code** don't have one. The interfaces Yardlet runs them through have no field for a session's MCP servers; what they load comes from their configuration. Their tasks in Yardlet run without the tools. I'd rather leave those tasks without the tools than write to the agents' settings.

## Antigravity loaded it, and kept a note

Antigravity nearly worked. Its CLI loads `.agents/mcp_config.json` from any folder passed with `--add-dir`, so Yardlet could pass a folder of its own, and the server loaded. Then I looked at what the CLI writes down. It records the folder in the conversation's `workspace_uris`, and when you continue that conversation in a terminal, it brings the folder back and tries to load the server again. A conversation continued outside Yardlet still made the CLI try to load Yardlet's server. I reverted that the same day, before it reached a release.

Since then the question I ask is not whether the server loads but what the agent writes down about it. For the three above, the server is in none of their files. Their transcripts keep the calls the agent made to the tools, as they keep any tool call; a session resumed outside Yardlet simply doesn't have the tools any more.

## Keeping the token to its session

The server itself does little. It asks the running app for the task's tool list and forwards each call over a local socket; the app drives the browser and the connectors. Each session gets a random 256-bit token in the server's environment. The app runs a call only when the token and the task ID match and the process that connected runs under the agent Yardlet runs for it: that task's Claude Code process, one of the Codex App Servers Yardlet started, or Yardlet itself for an ACP agent. Another process of the same user could read the token from the environment, but not call with it from elsewhere. Approvals stay with the agent, Claude's permission card or Codex's approval policy; Yardlet doesn't ask a second time.

## What is left when you remove it

Nothing in the agents' settings. Yardlet's own things are listed in the README: `~/.yardlet` (tasks, drafts), `~/Library/Application Support/Yardlet` (browser profiles), its logs and caches, and the Keychain items named Yardlet for the connectors. If you enabled the option to keep tasks running with the lid closed, turn it off before deleting the app. macOS keeps the app's background item after the app is gone.
