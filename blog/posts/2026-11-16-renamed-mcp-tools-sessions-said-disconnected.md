---
title: "I renamed my MCP tools, and 8 of 20 resumed sessions decided the server was down"
slug: renamed-mcp-tools-sessions-said-disconnected
date: 2026-11-16
description: "After I merged per-account MCP tools into single tools, 8 of 20 resumed Claude Code sessions reported that the server was disconnected and stopped calling tools, even though the server never went down."
---

At 02:30 on November 8, I installed a new build of [Yardlet](https://github.com/zzunkie/yardlet) on my Mac and restarted the app. Yardlet is a free, open-source Mac app I make that runs coding agents such as Claude Code and Codex side by side in one window. After the restart, my Claude Code sessions resumed.

At 03:10, I wrote to my coordinator session (an agent session that hands work to the other sessions) in Korean, asking, "The sessions are all saying they got disconnected. What's going on?" At 03:13 I wrote again, "It's the first time sessions say that when they resume."

The coordinator first called it cleanup after the restart that would recover by itself. Then it came back and said that was wrong, and held the Yardlet 0.11.10 release just before publishing until the cause was understood.

## Why the tool names changed

Yardlet runs its own MCP server for the agents it starts, with connectors such as Gmail, Google Calendar and Google Drive. Until November 8, every connector account got its own copy of every tool, with the account in the tool's name. I have 6 Google accounts connected. Having 39 functions across 6 accounts made 234 Google tools alone, which was 45% of the 517 tools in total.

Having all those copies got in the way when an agent searched for tools. In a Codex tool search, 8 slots came back filled by per-account copies of the same function, which pushed out other tools the agent needed.

The change was to expose one tool per function, with a required `account` argument instead of putting the account in the name. With that change, 517 tools became 322, and the list of tool names Claude Code loads into every session got 42% shorter. The main reason was accuracy, not cost, though permission lists and skills that named the old tools had to move to the new names. When my coordinator session explained the change on November 6, I answered, "Oh, so the new way is much better."

## What the 20 resumed sessions actually saw

Once the 0.11.10 release was held, a separate investigating session went through all 20 resumed sessions. In every one of them, the 322 tools were there, and there were no failed or pending MCP servers (`failedMcpServers` and `pendingMcpServers` were empty). Every session that actually called a tool after the notice succeeded, and one session made 88 calls.

The tools that had disappeared numbered 195, and they were only the old per-account names that had been merged away. Multiplying 39 functions by 5 removed per-account copies gives 195, the same as 517 minus 322.

The disconnect notice came from how Claude Code describes missing deferred tools on resume. When a resumed session's deferred tools are no longer in the tool list, Claude Code describes them as tools whose "MCP server disconnected", whatever the server's state is. When there are more than 30 of them, it shortens the list to `mcp__yardlet__* (195)`. Next to "MCP server disconnected", that line reads as if the whole server had dropped.

Out of the 20 resumed sessions, 8 said they were disconnected, and those sessions did not try a call. Instead, they worked around tools that were still running.

One coordinator session had an approved deployment to hand to the session that owned that work. Believing the tools were gone, it ran the deployment itself. The result was fine, and only who did it changed. My promotion session said the browser tools were gone and put off a Search Console check, until another session wrote to it that the tools still worked.

## A second problem in the conversation records

Checking the sessions also showed a second problem from the rename. Claude Code stores the tool definitions a session loaded in the conversation record (`deferred_tools_record`) and reuses them when the session resumes. Sessions that had loaded a Google tool before the update still had the old definition with no `account` argument, so their first call was rejected. That happened in 3 of 17 sessions.

Yardlet does not edit the agents' own conversation records to fix this, because those records belong to the agent. Instead, a rejected call now names the valid `account` values in the error response, so the next call recovers in one step. That change went into [pull request #613](https://github.com/zzunkie/yardlet/pull/613), and Yardlet 0.11.10 went out publicly that evening. The 0.11.10 release notes also say that Claude Code tasks continued from before the update may say once that Yardlet's tools disconnected.

Looking back at the record from that night, renaming a tool changed what the client told the agent, not only what the agent could call. Those 8 sessions trusted the status line instead of trying one call, while on the rejected calls, an error message that says what to send instead let the agent recover by itself.
