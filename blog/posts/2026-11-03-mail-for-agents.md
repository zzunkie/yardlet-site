---
title: "Handing my mail to coding agents, and keeping Send for myself"
slug: mail-for-agents
date: 2026-11-03
description: "Yardlet 0.11.8 adds a mailbox for Gmail, Outlook and IMAP accounts. Agents read a thread and write the reply as a draft through the account's connector; every send goes through the agent's approval."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents like Codex and Claude Code in one window.

I used to do my mail in Apple Mail. When I moved to a new Mac this week, my accounts didn't come over with it, and while setting them up again I realized I hadn't been reading mail there or writing replies there for a while. Agents in Yardlet were reading the threads through its Gmail and Outlook connectors and writing the replies as drafts. The mail app wasn't where I worked with mail anymore, so mail belonged in the workbench, next to the agents.

Yardlet 0.11.8 adds a mailbox. It is off by default. Settings › General › Mailbox turns it on, and the sidebar gets Mail next to Tasks and Personal agents. This post covers what it keeps, how a thread gets to an agent, who presses Send, and why Naver Mail needed IMAP.

## It reads the service and keeps almost nothing

The mailbox uses the sign-in the connector already has. Gmail is read through the Gmail API with the `gmail.modify` scope the connector asked for, Outlook through Microsoft Graph with `Mail.ReadWrite` and `Mail.Send`. Nothing more is requested, and the connector and the mailbox share one token.

Mail stays on the service. The mailbox reads a list when it is shown and keeps it in memory: the first page of each inbox, the folders a window opened, the last 30 threads. On disk it writes one thing per account, how far it has read the inbox's history (a Gmail history ID, a Graph delta link, an IMAP inbox's next UID), so mail that came while Yardlet was closed is still announced. No subject, address or line of a message goes to disk or to the log.

New mail is checked once a minute: `users.history.list` for Gmail, which costs 2 quota units, the inbox's delta query for Outlook, `STATUS` for IMAP. No model is involved. Mail that lands in Gmail's Primary tab or Outlook's Focused inbox becomes a notification.

HTML mail is drawn with scripts off, no cookies or storage, and a content rule that blocks every `http` and `https` load until I choose **Show images** for that message, so a tracking pixel has nothing to report. If the rule can't be compiled, the message is shown as text.

## Handing a thread to an agent

**Ask an agent** on a thread opens a new chat with the thread named in the composer:

```text Composer
Subject: October invoice
From: Dana Kim <dana@example.com>
Account: me@example.com · thread 19a3f0c2e1b4d5a6, read with `gmail_get_thread`
```

Then I write what I want done. The message itself is not pasted in. The agent reads it with the connector tool on that line, so it sees the thread as the account has it now, and a stranger's words don't land where my instructions go.

From there the agent works with the connector's tools as before. It can search the account, read other threads for context, and write a reply with `create_draft`. The draft is saved in the account's own Drafts folder, so it shows in the thread in the mailbox, under an orange **Draft**, and in any other app that reads the account.

## Who presses Send

On a draft in the mailbox I get **Send**, **Edit** and **Discard**. Send sends the draft as it was saved, so an HTML reply the agent wrote goes out as it is. Edit continues it as plain text with its recipients, blind copies and files. My own Send waits five seconds, during which **Undo** brings the message back.

The agent can send too, but not on its own say. The send tools (`send_draft` and `send_message`) are on the list of tools that go through the agent's approval each time. In Claude Code the request card has no "Always allow". For Gmail and Outlook it shows the recipients, the subject and the first 1,200 characters of the body, and when the agent sends a Gmail draft by its ID, Yardlet reads the draft from Gmail first and shows it instead of the ID. Codex decides from the task's approval settings and the tools' annotations, and ACP agents use their own MCP approval. Yardlet keeps no approval rules of its own. A task running with permissions bypassed is not asked, for these tools as for any other.

## Naver Mail has no API

Gmail and Outlook have APIs. A lot of mail in Korea lives at Naver, Daum or Kakao, and none of them has an API that Yardlet can read mail through. What they all have is IMAP and SMTP with an app password, the way Apple Mail and Thunderbird add them. So that is the third kind of account: Settings › Connectors › Add connector › **Mail (IMAP)**.

I type the address, and the address picks the service: its IMAP and SMTP servers, the user name (for iCloud, the part before the `@`), and what the service wants done on its website first, each step with a link. Usually that is turning on two-step verification, making an app password, and for Naver, Daum, Kakao and Zoho, switching IMAP on. NAVER WORKS, iCloud, Yahoo, AOL, Fastmail and Proton Mail Bridge are on the list too, and **Other IMAP server** takes the servers by hand.

**Connect** signs in to the IMAP server and to the SMTP server once each and signs out again, reading and sending nothing. Only when both accept the password is the account added. The app password goes into the Keychain and nowhere else, not into a file, the log or a command line. The servers and the address aren't secret, so they're in the connector's record. Every connection is TLS from the first byte or upgraded with STARTTLS before signing in, with the certificate checked against the server's name; a server that offers neither isn't used.

IMAP leaves more to the client than the APIs do. It has no threads, so each message is a line of its own. Folders are found by their special-use flags, or by the names services give them in English and Korean (보낸편지함, 임시보관함, 스팸편지함, 휴지통), and their names come in IMAP's modified UTF-7. Messages are read with `BODY.PEEK`, so opening one doesn't mark it read unless I opened it in the mailbox. A draft is a message appended to Drafts with its own `From`, `Date` and `Message-ID`. Sending goes over SMTP to every recipient with the Bcc line taken out, and a copy goes into Sent unless the server already put one there, found by its `Message-ID`.

Agents get five tools for such an account, named like Outlook's: `search_messages`, `get_message`, `list_folders`, `create_draft` and `send_draft`. There is no delete, and `send_draft` asks before every call.

## Turning it off

Turning the mailbox off stops the check, closes what's open, forgets every list and thread and the message being written, and removes the history markers on disk. The connectors and their Keychain items stay, since they belong to Settings › Connectors, where removing an IMAP account deletes its password too. The app password itself stays valid at the service until you delete it there.

The mailbox is documented in [docs/MAILBOX.md](https://github.com/zzunkie/yardlet/blob/main/docs/MAILBOX.md), and the connector side in [docs/CONNECTORS.md](https://github.com/zzunkie/yardlet/blob/main/docs/CONNECTORS.md).
