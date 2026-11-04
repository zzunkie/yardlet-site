---
title: "What moving a Claude Code task to another account costs"
slug: moving-a-task-costs-its-cache
date: 2026-11-05
description: "A task that moves to another account leaves its prompt cache behind, and the next request writes the whole conversation again. I measured it on 381,700 requests from my own transcripts, and Yardlet now moves a task only when that costs nothing, or when a limit has stopped it anyway."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents like Codex and Claude Code in one window.

In the [last post](https://yardlet.app/blog/accounts-with-room-left.html) I wrote that Yardlet starts each new task on the account with room left. I didn't say what that meant for a scheduled run that continues an existing Claude Code task: if the task's account was nearly spent, 10% or less left in a window, the run moved the task to another account first. The task keeps its conversation either way, because Yardlet's account folders share Claude Code's history. I had assumed the move was free. It isn't, and I wanted to know by how much before I kept the rule.

## The cache stays behind

Claude Code sends its requests with a prompt cache. In my transcripts the main conversation has been cached with the one-hour lifetime since mid-October, and subagents use the five-minute one. The cache belongs to the workspace that wrote it, so an account can't read what another account cached. When a task moves, its first request on the new account writes the whole conversation into the cache again.

On Opus 5.5, input is $4 per million tokens, a one-hour cache write is twice that, and a cache read is a twentieth of it, $0.20. The same tokens cost about forty times more to write than to read. One part survives the move: Claude Code marks the first block of its system prompt with a global cache scope, and that block still reads from the cache on the new account. In the moves I looked at it was 26,000 to 41,000 tokens; I use 30,000 below. Everything after it is written again.

So moving a task once costs about `(context - 30,000) × $7.80 per million tokens`:

- 100,000 tokens of context: about $0.55
- 300,000: about $2.10
- 500,000: about $3.70
- 900,000: about $6.80

For the tasks I looked at, that one request costs as much as about thirty of the task's ordinary requests.

## What 381,700 requests said

Claude Code keeps every conversation as JSONL under `~/.claude/projects`, and every assistant line carries `message.usage` with input tokens, cache writes by lifetime, cache reads and output. Since early October most lines also carry `cache_miss_reason`, the API's word for why a request didn't read the cache. `previous_message_not_found` within the hour is the one I read as an account change. I read every conversation file touched since October 1: 3,472 files and 381,700 requests after removing duplicates. No model turn, no sign-in touched.

A cache loss, as I counted it, in main conversations only: the previous request had at least 30,000 tokens of context, this one read less than half of that, the model was the same, and the context didn't shrink. The lost tokens are the smaller of what this request wrote and what the previous one had cached, and the extra cost is those tokens at the write price minus the read price.

- Moves between accounts: 44 of them, $164 in API-equivalent terms, 0.4% of the $41,099 those five weeks add up to.
- Caches that simply expired because the task sat idle for more than an hour: $5,632, 13.7%.
- Restarting the CLI on the same account keeps the cache. Of 460 restarts within an hour of the previous request, 374 read the cache as if nothing had happened; 18 were account changes, and 67 lost it because the system prompt, the messages or the tools had changed.

Yardlet itself had logged only six moves, the ones its scheduled runs made, and three of those were tasks that had sat idle for five to nine hours, so their cache was gone before the move. The other 41 I found through the diagnostics. One of the logged ones is the case I had worried about: on November 2 at 11:25 at night a scheduled run picked up a task 2.4 minutes after its last request, moved it, and the next request wrote 390,000 tokens, $3.02, 33 times that task's usual request.

Of the 15 moves that followed a limit, 8 had a reset coming in 15 to 50 minutes. Waiting would have kept the cache alive. The other 7 faced a reset hours away or a weekly limit. The new account still paid the write, but waiting on the old one would have let the hour pass and the cache expire, so the move lost nothing that waiting would have kept.

Claude Code's automatic compaction ran 167 times in those weeks, taking a median 970,000 tokens of context down to 90,000, and the first request after it writes the cache fresh on any account. A task that has just compacted could move for nothing, though Yardlet doesn't use that yet: compaction happens inside a turn, and a move never cuts into one. What doesn't help is waiting for the turn to end: the cache runs from the last request, not from the end of the turn.

## What Yardlet does now

Settings › Accounts has a switch, "Move tasks to an account with room", on by default, and it moves a Claude Code task only when the move costs nothing or the task can't go on where it is:

- An idle task on a nearly spent account moves once its cache has expired, an hour after its last request, without starting its CLI.
- A task that a limit stopped moves and continues on an account with room, unless the limit resets within the day and before its cache would expire. Then the task stays and continues at the reset. A card I armed myself also keeps its task where it is.
- A task whose cache is still alive stays where it is until a limit stops it or the hour passes. A scheduled run that continues such a task leaves it on its account.

A move never cuts into a turn. A second switch next to it, "Continue automatically at usage limit", is on by default too: a Claude Code task stopped by a limit that resets within the day continues by itself at the reset, as the CLI does in a terminal, instead of waiting for me to flip a switch on the card. The two work together: a task whose limit resets after its cache would expire moves to an account with room right away, and one whose limit resets sooner waits.

This is on `main` and goes out with the next release.

## What I can't say from this

The dollars are API-equivalent. On a subscription nothing is billed per token; a move spends part of a limit window instead, and by my rough estimate a 500,000-token move is under one percent of a five-hour window and far less of a weekly one.

The 41 unlogged moves are inferred from the diagnostics, so a cache the server dropped early would look the same. And Yardlet doesn't move Codex tasks between accounts, so I measured none.

The rule is written up in [docs/PROVIDER_CONNECTIONS.md](https://github.com/zzunkie/yardlet/blob/main/docs/PROVIDER_CONNECTIONS.md) ("Moving tasks to an account with room").
