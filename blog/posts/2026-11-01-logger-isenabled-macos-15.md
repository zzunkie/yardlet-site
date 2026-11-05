---
title: "A Logger symbol missing on macOS 15 kept my Mac app from launching"
slug: logger-isenabled-macos-15
date: 2026-11-01
description: "For four days Yardlet quit at launch on macOS 15. The SDK marks Logger.isEnabled(type:) as available since macOS 11, but macOS 15.6.1's libswiftos doesn't have it."
---

I make [Yardlet](https://github.com/zzunkie/yardlet), a free, open-source Mac app for running coding agents like Codex and Claude Code in one window. It says it needs macOS 15 or later. For four days it quit at launch on macOS 15, and I didn't know.

## How I found out

On October 31 I was getting my company MacBook ready for a performance comparison. That Mac is still on macOS 15.6.1. Yardlet quit the moment it launched. No window, just a crash report. My first thought was that the company Mac was just too old.

```text Crash report
Termination Reason: DYLD, Symbol missing
Symbol not found: _$s2os6LoggerV9isEnabled4typeSbSo0a5_log_E2_ta_tF
Expected in: /usr/lib/swift/libswiftos.dylib
```

That symbol is `Logger.isEnabled(type:)` from the `os` module. I used it in one place, to skip building debug messages about text selection when nobody is reading debug logs.

I downloaded the public disk images of 0.11.0, 0.11.4 and 0.11.5 and checked them with `nm -u`. All three import it. 0.11.0, the first public release, went out on October 27. My own Mac runs macOS 27, so I never saw it.

## Why it compiled

The deployment target is macOS 15, so I expected an availability error if I called anything newer. In Xcode 27.1's SDK, `Logger` is marked available since macOS 11, and `isEnabled(type:)` has no availability of its own (shortened):

```swift
@available(macOS 11.0, iOS 14.0, watchOS 7.0, tvOS 14.0, *)
public struct Logger : @unchecked Sendable {
  // ...
  public func isEnabled(type: OSLogType) -> Bool
```

So the compiler treats it as there since macOS 11. But the macOS 15.5 SDK that comes with the Command Line Tools has no such symbol in `libswiftos.tbd`, the 27 SDK has it, and `libswiftos.dylib` on macOS 15.6.1 doesn't export it. I haven't checked macOS 26.

> **Update, November 5:** Quinn from Apple Developer Technical Support has since checked macOS 26. The symbol is missing on 26.2 and there on 26.7.1, and Apple's bug records suggest it arrived in 26.4. He also filed a bug about the availability mismatch. [His answer on the Apple Developer Forums](https://developer.apple.com/forums/thread/855301?answerId=914801022#914801022).

## The fix

`OSLog` has its own `isEnabled(type:)`, which goes to the C function `os_log_type_enabled`, there since macOS 10.12. So I keep an `OSLog` handle, make the `Logger` from it, and ask the handle:

```swift
static let logHandle = OSLog(subsystem: bundleID, category: "conversation-selection")
static let log = Logger(logHandle)

guard logHandle.isEnabled(type: .debug) else { return }
```

## Checking the other imports

I didn't want to find the next one the same way. On the macOS 15.6.1 Mac I listed the symbols the executable imports without weak linking, and checked each one against what its system library exports there. A rough version of the script (it doesn't check exit codes):

```python check-imports.py
import re, subprocess, sys

def run(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout

def short(path):
    name = re.sub(r"\.dylib$", "", path.split("/")[-1])
    return re.sub(r"(\.[A-Z0-9]+)+$", "", name)

binary = sys.argv[1]
wanted = {}
for line in run("dyld_info", "-imports", binary).splitlines():
    m = re.match(r"\s+0x[0-9A-F]+\s+(_\S+)\s+(\[weak-import\]\s+)?\(from (\S+)\)", line)
    if m and not m.group(2):
        wanted.setdefault(m.group(3), set()).add(m.group(1))

for line in run("dyld_info", "-dependents", binary).splitlines():
    path = line.strip().split()[-1] if line.strip() else ""
    if not path.startswith(("/usr/lib", "/System")) or short(path) not in wanted:
        continue
    libraries = [path] + [l.split()[-1] for l in run("dyld_info", "-dependents", path).splitlines() if "re-export" in l]
    exported = set()
    for library in libraries:
        exported |= set(re.findall(r"(_\S+)", run("dyld_info", "-exports", library)))
    for symbol in sorted(wanted[short(path)] - exported):
        print(short(path), run("xcrun", "swift-demangle", "--compact", symbol).strip())
```

It follows direct re-exports, since SwiftUI re-exports SwiftUICore on macOS 15. For 0.11.5, with 4,261 strong imports, it printed one line: `libswiftos os.Logger.isEnabled(type: __C.os_log_type_t) -> Swift.Bool`.

0.11.6 went out the same night. Before publishing it I copied the notarized disk image to the macOS 15.6.1 Mac. The script printed nothing for its 4,291 imports, and the app stayed up when I launched it with an empty home folder.

## What changed

Now every release gets this check and a launch on that macOS 15 Mac before it goes out. A CI job that launches the app on the oldest supported macOS is planned but not built yet.

I had thought of the deployment target as something the compiler would hold me to. It only holds me to what the SDK says, and here that was macOS 11.
