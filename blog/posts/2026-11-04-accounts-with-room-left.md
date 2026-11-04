---
title: "Starting each agent task on the account with room left"
slug: accounts-with-room-left
date: 2026-11-04
description: "I keep work and personal accounts for Claude Code and Codex. Yardlet reads each account's limits from the CLI itself and starts a task on the one with room left, instead of asking me every time."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents like Codex and Claude Code in one window.

I have more than one account for both agents, work and personal, and I usually have about ten sessions going. On November 1 my sessions ran into a limit three times: a five-hour limit at 5:21 in the morning, "You've hit your weekly limit · resets 3am" at 9:27 at night, and another five-hour limit at 10:57. Each time the question was the same. Which account still has room?

## Every account's limits, read from the CLI

Settings › Accounts lists every sign-in with its five-hour and weekly windows and when each resets. Yardlet doesn't call the providers with a token of its own. It asks each CLI with the sign-in that CLI already has: Claude Code through its `get_usage` control request, which runs no model turn, Codex through its App Server's rate-limit read, and Antigravity CLI through `agy --print /usage`. A limit a CLI doesn't report is shown as not available, never as zero.

## The task picks the account

A new task's account menu says Automatic unless I pick one. A task an agent starts (a child task or a subagent), a suggestion I accept, or a new task I start on Automatic goes to the account with the most room left, and tasks started together spread across the accounts. The task's card says what was chosen and why:

```text Task card
work@example.com · Chosen automatically · 5 hour limit 12% used · Resets 3:00 PM
```

The account is stored with the task when it starts, so resuming it later uses the same one.

Scheduled runs check before they start. If the account a run would use has 10% or less left in a window, the run starts on the account with the most room instead, and if every account is nearly spent, on the one that frees up first. The run's line in the schedule's history names the account it went to and the one it replaced.

Two smaller things came from running into limits myself. Since 0.11.7, a Claude limit card offers Resume once the limit has reset, so I don't have to type "continue" when I come back. Since 0.11.8, choosing another account on a working task takes effect when its turn ends, and what I send meanwhile goes to the new account. Before, that choice was quietly ignored while a turn ran.

## Which agents can keep more than one account

- **Claude Code:** yes, a `CLAUDE_CONFIG_DIR` folder per account. Folders Yardlet makes share the default folder's conversation history, so a task can move to another account and keep its conversation.
- **Codex:** yes, a `CODEX_HOME` per account. Each keeps its own history, so an extra account joins automatic assignment only when I include it.
- **Kimi Code and Grok Build:** yes, with `KIMI_CODE_HOME` and `GROK_HOME`, the same way as Codex.
- **Cursor Agent and Antigravity CLI:** no. Each keeps its sign-in in one fixed Keychain item.

## What it doesn't do

Every account is one I signed in to myself in that agent's own CLI. Yardlet doesn't create accounts, copy a sign-in from one folder to another, or move a turn that is already running. It decides where the next task starts.

The rules are in [docs/NATIVE_SESSION_STORAGE.md](https://github.com/zzunkie/yardlet/blob/main/docs/NATIVE_SESSION_STORAGE.md) ("Automatic account assignment") and [docs/PROVIDER_CONNECTIONS.md](https://github.com/zzunkie/yardlet/blob/main/docs/PROVIDER_CONNECTIONS.md).
