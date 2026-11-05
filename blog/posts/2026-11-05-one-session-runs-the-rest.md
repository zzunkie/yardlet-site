---
title: "I talk to one session, and it runs the rest"
slug: one-session-runs-the-rest
date: 2026-11-05
description: "Andrej Karpathy wrote that he only talks to Claude now and did three things by hand. Yardlet's own development has run the same way for weeks: one long-lived session I talk to, child sessions it starts, and a few places where I still say yes. Almost none of what still lands on me is approving. Most of it is reading."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents like Codex and Claude Code in one window.

Last week Andrej Karpathy [built HackerTube](https://karpathy.bearblog.dev/hacker-tube/) in a morning and added a note on how he works now: "I don't actually do anything resembling traditional engineering anymore (read/write code, run commands in a terminal, or etc.), I only talk to Claude and have it do everything." The manual work on that project was three things: an API key from a Google Cloud screen, a VPS, a domain name. It read as familiar. That is how I have been working on Yardlet itself for a few weeks, so I had a session compare the two and tell me where they differ.

## One session I talk to

I have about ten tasks open in Yardlet at any time. One of them is a coordinating session for the Yardlet project that has been running since mid-October. I don't give it code. I tell it things like "the mail list should start folded when there are several accounts" or "is the long-command approval on the phone being fixed?", and it starts child tasks, each a session of its own in its own worktree, reviews what they send back, lands their pull requests on `main`, builds a signed build and stages it as an update on my Macs.

Two numbers from my own logs say how much of my talking goes through that one session. From October 16 to 31 I sent 128 messages from my phone to tasks on the Mac. 45 of them, 35%, went to the coordinating session; the next busiest task got 13. In those two weeks I answered zero approval requests and zero questions from the phone.

Last night is a fair sample of a day. Between my "I installed the update" and "archive the finished ones", the coordinating session landed a batch of pull requests, built and staged a signed build, and sent two defects its child tasks had reported to new child tasks. What came back to me that day was: paste this Mac's SSH key into a Windows PC, check whether a notification actually appeared on screen, approve a test email, install the build. Karpathy's list was an API key, a server and a domain. Both lists come down to things that need my own hands or my own accounts, done while the agent works.

## Where it differs

**A session that lives for weeks.** HackerTube took about two hours. My coordinating session has carried the project since mid-October, and what carries it is a handoff file next to the code, not the session's memory: a dated section a day with what landed, which build is staged on which Mac, what is waiting on CI and what is waiting on me. A restart or a compaction starts from that file. Keeping the session alive that long is mostly keeping that file current.

**The workers are sessions of their own.** Karpathy had Claude fan Sonnet out over the Hacker News comments with Claude Code's Workflow feature, which runs its workers from inside the session that started them. My child tasks are full sessions with their own worktree and their own history. They show up in the sidebar next to everything else, and I can open one and talk to it directly without going through the coordinator. That makes it easy to step in, and it is also where the extra reading comes from.

**I kept a few places where I say yes.** He gave Claude the server's IP and let it deploy, which fits a personal site with no accounts and nothing to break for anyone else. I let the coordinating session merge and build on its own, but a production deploy, a public release, anything other people will see, and deleting data still wait for an explicit yes from me, because a mistake there reaches people who use the app or work with me. On October 28 an agent asked whether a sentence belonged on the site and in the README. I answered with a one-line musing that was really a question, it read it as a yes, deployed the site and merged the README change. Since then an agent acts only on a clear yes or an unambiguous instruction.

## How far to go

Reading his note, the question I actually had was whether to take my hands off further. So I asked a session to count what was still landing on me.

It wasn't approvals. I hadn't approved anything from my phone in two weeks, and that morning no task was waiting for a yes from me. It was reading. I had eleven unread tasks in the sidebar, and seven of them were child tasks. A child task reports to the session that started it before it ends, so by the time I opened one, its result had already reached the coordinator and come back to me in the coordinator's report. I was reading the same result twice.

The cause is in how Yardlet marks things read: a task's unread mark clears when a window shows the task, and a session reading another session's result through a tool doesn't clear it. Clearing the mark when the coordinator reads a child would fix my sidebar. I decided against it. It would change what every Yardlet user sees without any sign of it, and someone who reads child results directly would miss them. It fits how I work, and other people may not like it, so it stays out of the app.

The fix went into my own instruction file instead: the session that started a child task archives it once the work has landed and nothing in it is waiting on me, and says in its report what it archived. The children are still in the archive if I want them, and finished child tasks stay out of my unread list.

That leaves what Karpathy described: one session I talk to, a short list of things only I can do, done in between its work, and a yes from me where a mistake would reach other people. Yardlet is the window those sessions live in, and the coordinating session runs the others with the same task tools any agent gets in Yardlet.
