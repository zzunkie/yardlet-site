---
title: "Codex reviewed Claude Code's patch three times: two real regressions, one wrong call"
slug: codex-reviewed-claude-codes-patch
date: 2026-11-08
description: "Before sending a five-line fix to swift-winrt, I had Codex review the patch Claude Code wrote, three times. Two findings were real regressions. The third was wrong, and chasing it cost two needless changes."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app that runs coding agents such as Claude Code and Codex in one window. My setup that week, in the words I used at the time: "claude code writes, codex reviews". A second model catches things the first one glosses over.

On October 31 I was trying a Windows version of Yardlet built with Swift and WinUI 3, on top of [swift-winrt](https://github.com/thebrowsercompany/swift-winrt), the Swift projection for WinRT.

## The bug in `NavigationView.MenuItems`

In the WinUI 3 app, on Windows App SDK 1.7.250909003, `IVector<Object>.IndexOf` on `NavigationView.MenuItems` did not find an item appended through the projection. It did not even find the value `GetAt` had just returned. `IndexOf` on a `UIElementCollection` found its element.

The cause was in swift-winrt's support code. Passing a projected runtime class where a WinRT API takes `Object` gave the callee a Swift-implemented wrapper made for that conversion, not the object. The wrapper answers `QueryInterface` for `IUnknown` with itself, so each conversion had its own COM identity, and native code that compares objects by COM identity did not match them.

The fix Claude Code wrote was five lines: `AnyWrapper.toABI` passes a `WinRTClass` as the `IInspectable` pointer `_getABI()` returns. It also wrote tests in the repository's own style. With the tests alone, 2 of 111 failed; with the fix, none did.

## Why a second review

The patch was going to someone else's project. My note to the session that evening, translated from Korean: "It's external work, so let's check it properly once more before we send it."

The reviewer was Codex (GPT-6 Astra at extra-high reasoning effort), which had not written the fix. From the Claude Code task, Yardlet's `run_agent` tool ran it as a subagent and returned its answer to the same conversation. It got the base commit, the diff, the draft pull request text and the two test results, tests alone and tests with the fix, but not the author's conclusion. Each time, Codex said it had read the source and had not rerun the Windows tests itself.

## Round 1: `GetRuntimeClassName` on a composable subclass

The first review came back at 14:05 UTC with a blocking finding.

For a Swift subclass of a composable class with no overrides interface, such as the test component's `BaseNoOverrides`, the object passed through the new path is a `WinRTClassWeakReference<BaseNoOverrides>`. The shared `IInspectable` vtable's `GetRuntimeClassName` casts it to `WinRTClass`, the cast fails, and the object reports `WinRTClassWeakReference<…>` instead of its WinRT class name. Before the change, the old wrapper held the real subclass and reported the right name. Code that looks up types or XAML metadata by runtime class name would get the wrong one.

A test for that case failed in CI before the fix and passed after it. The vtable's `GetRuntimeClassName` now looks through the weak reference.

## Round 2: an access violation in `Resolve`

The second review, at 14:57 UTC, found another blocking problem.

`Resolve` in the support code's weak reference passed the pointer from `toABI` to the static `AnyWrapper.queryInterface`, which reads that pointer as a Swift wrapper. After the first change, the pointer can be the native WinRT object, which has no such layout.

It reproduced. With the `toABI` and `GetRuntimeClassName` changes but not this one, the test process exits with `0xC0000005`, an access violation, right after `testResolveProjectedClass` starts, with no test summary. `Resolve` now calls `QueryInterface` through the vtable of the pointer `toABI` returns, and a new `ReferenceTarget` runtime class in the test component covers it.

## Round 3: a wrong call on `GetWeakReference`

The third review, at 15:27 UTC, raised a third blocking claim: that `GetWeakReference` would now fail, because it unwraps the object through a `QueryInterface` for Swift's own interface, so the "all tests pass" result could not be right for this path.

The code and CI showed the claim was wrong, and it was rejected. While chasing it, two changes had gone in that were not needed. Both were reverted.

## Where it stands

The pull request went up at 17:33 UTC the same day: ["Pass projected runtime classes as themselves where WinRT takes an Object"](https://github.com/thebrowsercompany/swift-winrt/pull/272). The five lines grew to 16 files, +179 −6, most of it tests and regenerated test bindings. On a GitHub Actions Windows runner the test app runs 112 tests with 1 skipped and no failures, on Swift 6.2 in debug and Swift 6.4.1 in release; `main` has 110.

The pull request also states a behaviour change. For a projected object that is not a Swift subclass, an `Object` parameter now gets the WinRT object itself, so reading it back gives a different Swift instance (`===` is false), and `==` compares COM identity.

Yardlet's own copy of the patch was replaced with the reviewed version. As of November 8 the pull request has no comments or reviews, and only a static scan has run on it; the build and test workflows have not run on the fork.

## What I do now

Asking the agent that wrote a change to check it again tends to check its own assumptions again. The second agent started from the code and the results, and found two real bugs, one of them a crash, that the authoring session and a passing test suite had missed.

So a reviewing agent gets the diff and the test results, not my conclusion. And a reviewer can be wrong with the same confidence as when it is right: every blocking finding gets a reproduction or a check in CI before it is accepted or rejected. The wrong call in round three still cost time and two changes that had to be undone.

## How it runs

In Yardlet both agents run from their own CLIs with the sign-ins they already have. A Claude Code task can run Codex as a subagent with `run_agent` and read its answer in the same conversation, or the two tasks can sit side by side in a split view. In a Git repository each task can start in its own worktree. The setup is in the [README](https://github.com/zzunkie/yardlet), or install it with `brew install --cask zzunkie/tap/yardlet`.
