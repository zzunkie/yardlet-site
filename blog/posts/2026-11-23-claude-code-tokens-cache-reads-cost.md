---
title: "98% of our Claude Code tokens were cache reads, but only 52% of the cost"
slug: claude-code-tokens-cache-reads-cost
date: 2026-11-23
description: "Across 8 days of Claude Code transcripts on my Mac, cache reads were 98% of the tokens but 52% of the API-equivalent cost, while cache writes and output were 35% and 13%."
---

On November 3 at 18:39 (Korea time), I wrote to my coordinator session (an agent session that hands work to the other sessions) in Korean, "It seems like people like monitoring stuff like token usage. Should we put it on the home screen or somewhere that fits?" At 18:49, I wrote again, "Let's find what people like and benchmark it."

[Yardlet](https://github.com/zzunkie/yardlet) is a free, open-source Mac app I make that runs coding agents such as Claude Code and Codex side by side in one window. A session looked at the usage pages in the agents' own apps and at the community tools that fill the same gap. The agents' own pages put the plan limit (percent used in the 5-hour and weekly windows) and the reset time first. They leave out which task or project used the tokens, when a limit runs out at the current pace, and the API-equivalent cost, which the community tools cover.

Four choices came back, covering a usage band on the Home screen, showing the API-equivalent cost on Home too, turning counting on by default, and keeping counts for a year. I left them to the coordinator, which took the recommended option for each.

## What 8 days of transcripts showed

Before building anything, the session read 8 days of Claude Code transcripts on my Mac, from October 27 to November 3, read-only.

In those 8 days, 98% of Claude Code's tokens were cache reads, but cache reads were only 52% of the API-equivalent cost. Cache writes were 2% of the tokens and 35% of the cost, output was 0.2% of the tokens and 13% of the cost, and new (uncached) input was under 0.01% of both. On November 17, a session re-counted the same 8 days with the shipped feature's own counts and got the same shares.

| Kind | Share of tokens | Share of API-equivalent cost |
| --- | --- | --- |
| Cache reads | 98% | 52% |
| Cache writes | 2% | 35% |
| Output | 0.2% | 13% |
| New input | under 0.01% | under 0.01% |

Claude Opus 5.5 made up 99.6% of those tokens. On Anthropic's public pricing page (as copied into Yardlet on November 3), its prices per million tokens are $4 for input, $5 for a 5-minute cache write or $8 for a 1-hour cache write, $0.20 for a cache read, and $20 for output. So a cache read costs 1/20 of new input, a cache write costs 25 to 40 times a cache read, and output costs 100 times a cache read.

These dollars are API-equivalent. A subscription does not pay them; it pays in plan limits, and the app labels the number "API equivalent". On the Home band and the usage page, we drew the bars in API-equivalent cost instead of tokens, and showed two bars for the split by kind, one for tokens above one for cost, so the two pictures sit next to each other.

## Where counting went wrong

Claude Code writes one transcript line per content block of a response, and every one of those lines carries the response's usage while the output grows to its final count. So each response (`message.id`) is counted once, taking its largest output.

A forked or branched conversation copies earlier responses into a new file. Our first idea was to recognize copies by the file's creation time, which did not work. Among the files from the last 3 days, 94 of 222 had a first response older than the file's creation time for reasons such as account folders being tidied up. Instead, we keep the last 14 days of response ids in a small SQLite file, and an id seen again adds only output not counted yet. The same id showed up in two files 152 times out of about 79,000.

Codex writes running totals, so each count is the difference from the one before, and a Codex subagent's file first replays its parent's history, which we skip. On my Mac, the first full read of 15.4 GB of transcripts took 139 seconds in a debug build, wrote a 13 MB counts file, and matched a separate Python count on requests per day.

## Plan limits and what we left out

We never estimate plan limits from local tokens and show only the limit readings the provider itself returns. Tools that estimate the limit from local token counts have reports that the estimate does not match the real limit, including one user shown at 198% of their plan. Our "runs out in" time comes from two of the provider's own readings of the same window at least 15 minutes apart within the last hour. Reading the limits every 5 minutes while Home was open started three accounts' CLIs 36 times an hour, so we changed that to every 15 minutes.

We also skipped speed numbers like tokens per minute, since tools that fill this gap rarely get cited for them and one "runs out in" line answers the same question. We left out leaderboards and share cards because they would have to send data off the Mac, and gather file changes every few seconds rather than updating on every streamed token. Counting shipped on by default in Yardlet 0.11.9, and turning it off deletes the counts folder (`~/.yardlet/usage/`).
