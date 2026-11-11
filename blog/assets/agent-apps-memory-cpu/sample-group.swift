// Samples one app's processes once a second and prints one JSON object: for each second, each
// category's CPU % (100 = one core) and memory, and for the whole run each category's mean and 95th
// percentile CPU, median and largest footprint, and the processes seen.
//
// A process is the app's when its executable is under the app's bundle, when macOS charges it to a
// process from the bundle (its responsible process: the WebKit services a web view uses, the shells,
// servers and CLIs the app starts, and everything those start), when it runs from under the app's
// home or is charged to one that does (a helper app the app copies into its data folder and starts
// apart from itself, as Orca does its terminal host), or when its name contains one of the extra words
// (a daemon the app leaves running apart from it). Each is put in one category: `agents` when it runs
// an agent CLI (its executable or an argument under an `agents` path, or its name equal to an `agents`
// word), `app` when it runs from the bundle, `daemon` when it runs from the home, `webkit` for the
// system's WebKit services, the extra word's category, or `other`. `total` adds every category but
// `agents`: the agent CLIs here are the bench's fakes and say nothing about the app. Processes are told
// apart by PID and start time, so a reused PID is a new process.
//
// usage: sample-group <seconds> app=<bundle path> [home=<home path>] [agents=<path or name> ...]
//                     [<category>=<word> ...]
//   e.g. sample-group 120 app=/path/Orca.app agents=/path/home/bin agents=codex daemon=hmux-runtime
import Darwin
import Foundation

let arguments = Array(CommandLine.arguments.dropFirst())
let rules: [(category: String, match: String)] = arguments.dropFirst().compactMap { argument in
    guard let equals = argument.firstIndex(of: "=") else { return nil }
    return (String(argument[..<equals]), String(argument[argument.index(after: equals)...]))
}
guard let seconds = arguments.first.flatMap(Int.init),
      let appPath = rules.first(where: { $0.category == "app" })?.match else {
    FileHandle.standardError.write("usage: sample-group <seconds> app=<bundle path> [category=<path or word> ...]\n".data(using: .utf8)!)
    exit(2)
}
let agentRules = rules.filter { $0.category == "agents" }.map(\.match)
let homePath = rules.first(where: { $0.category == "home" })?.match
let wordRules = rules.filter { !["app", "home", "agents"].contains($0.category) }

typealias ResponsibleFunction = @convention(c) (pid_t) -> pid_t
let responsible: ResponsibleFunction = {
    guard let symbol = dlsym(dlopen(nil, RTLD_NOW), "responsibility_get_pid_responsible_for_pid") else {
        FileHandle.standardError.write("this macOS does not say which app a process is charged to\n".data(using: .utf8)!)
        exit(1)
    }
    return unsafeBitCast(symbol, to: ResponsibleFunction.self)
}()

struct Key: Hashable { let pid: pid_t; let start: UInt64 }
struct Reading { let cpuNanoseconds: UInt64; let footprint: UInt64 }

func allPIDs() -> [pid_t] {
    let count = proc_listallpids(nil, 0)
    var pids = [pid_t](repeating: 0, count: Int(count) + 64)
    let filled = proc_listallpids(&pids, Int32(pids.count * MemoryLayout<pid_t>.size))
    return Array(pids.prefix(Int(max(filled, 0))))
}

func path(_ pid: pid_t) -> String? {
    var buffer = [CChar](repeating: 0, count: 4096)
    let length = proc_pidpath(pid, &buffer, UInt32(buffer.count))
    guard length > 0 else { return nil }
    return String(decoding: buffer.prefix(Int(length)).map { UInt8(bitPattern: $0) }, as: UTF8.self)
}

/// The process's arguments, its executable's path first, from KERN_PROCARGS2.
func commandLine(_ pid: pid_t) -> [String] {
    var name: [Int32] = [CTL_KERN, KERN_PROCARGS2, pid]
    var size = 0
    guard sysctl(&name, 3, nil, &size, nil, 0) == 0, size > MemoryLayout<Int32>.size else { return [] }
    var buffer = [UInt8](repeating: 0, count: size)
    guard sysctl(&name, 3, &buffer, &size, nil, 0) == 0 else { return [] }
    let count = buffer.withUnsafeBytes { $0.load(as: Int32.self) }
    // argc, the executable's path, padding, then argc NUL-terminated arguments.
    let fields = buffer[MemoryLayout<Int32>.size..<size].split(separator: 0, omittingEmptySubsequences: true)
    return fields.prefix(Int(count) + 1).map { String(decoding: $0, as: UTF8.self) }
}

func startTime(_ pid: pid_t) -> UInt64? {
    var info = proc_bsdinfo()
    let size = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, Int32(MemoryLayout<proc_bsdinfo>.size))
    guard size == Int32(MemoryLayout<proc_bsdinfo>.size) else { return nil }
    return info.pbi_start_tvsec * 1_000_000 + info.pbi_start_tvusec
}

func reading(_ pid: pid_t) -> Reading? {
    var info = rusage_info_v4()
    let result = withUnsafeMutablePointer(to: &info) { pointer in
        pointer.withMemoryRebound(to: rusage_info_t?.self, capacity: 1) { proc_pid_rusage(pid, RUSAGE_INFO_V4, $0) }
    }
    guard result == 0 else { return nil }
    var timebase = mach_timebase_info_data_t()
    mach_timebase_info(&timebase)
    let cpu = (info.ri_user_time + info.ri_system_time) * UInt64(timebase.numer) / UInt64(timebase.denom)
    return Reading(cpuNanoseconds: cpu, footprint: info.ri_phys_footprint)
}

func underApp(_ path: String) -> Bool { path.hasPrefix(appPath) }
func underHome(_ path: String) -> Bool { homePath.map { path.hasPrefix($0) } ?? false }
func ours(_ path: String) -> Bool { underApp(path) || underHome(path) }

/// The app's category for the process, or nil when it is not the app's.
func category(pid: pid_t, executable: String) -> String? {
    let name = (executable as NSString).lastPathComponent
    let word = wordRules.first { name.contains($0.match) }
    let charged = responsible(pid)
    guard ours(executable) || word != nil || (charged != pid && path(charged).map(ours) == true) else { return nil }
    let command = commandLine(pid)
    for rule in agentRules {
        if rule.hasPrefix("/") ? command.contains(where: { $0.hasPrefix(rule) }) || executable.hasPrefix(rule)
                               : name == rule || command.dropFirst().first.map({ ($0 as NSString).lastPathComponent == rule }) == true {
            return "agents"
        }
    }
    if underApp(executable) { return "app" }
    if underHome(executable) { return "daemon" }
    if executable.hasPrefix("/System/Library/Frameworks/WebKit.framework/") || name.hasPrefix("com.apple.WebKit.") { return "webkit" }
    return word?.category ?? "other"
}

/// The app's processes now, by key, with their category and path.
func members() -> [Key: (category: String, path: String)] {
    var found: [Key: (String, String)] = [:]
    for pid in allPIDs() where pid > 0 && pid != getpid() {
        guard let path = path(pid), let category = category(pid: pid, executable: path), let start = startTime(pid) else { continue }
        found[Key(pid: pid, start: start)] = (category, path)
    }
    return found
}

var previous: [Key: Reading] = [:]
var categories: [Key: String] = [:]
var previousTime = DispatchTime.now().uptimeNanoseconds
for (key, member) in members() {
    categories[key] = member.category
    if let now = reading(key.pid) { previous[key] = now }
}
var series: [[String: Any]] = []
var cpuByCategory: [String: [Double]] = [:]
var footprintByCategory: [String: [Double]] = [:]
var countByCategory: [String: [Double]] = [:]
var seen: [String: [String: Any]] = [:]
let fixedCategories = ["app", "daemon", "webkit", "other", "agents", "total"] + wordRules.map(\.category)
for second in 1...seconds {
    Thread.sleep(forTimeInterval: 1)
    let now = DispatchTime.now().uptimeNanoseconds
    let elapsed = Double(now - previousTime) / 1e9
    previousTime = now
    var current: [Key: Reading] = [:]
    var cpu: [String: Double] = [:]
    var footprint: [String: Double] = [:]
    var count: [String: Double] = [:]
    for (key, member) in members() {
        guard let reading = reading(key.pid) else { continue }
        // A process keeps the category it had when first seen.
        let category = categories[key] ?? member.category
        categories[key] = category
        current[key] = reading
        seen["\(key.pid)-\(key.start)"] = ["pid": key.pid, "category": category, "path": member.path]
        // A process that started during the second counts from its start.
        let used = Double(reading.cpuNanoseconds &- (previous[key]?.cpuNanoseconds ?? 0)) / (elapsed * 1e9) * 100
        let memory = Double(reading.footprint) / 1_048_576
        for name in category == "agents" ? [category] : [category, "total"] {
            cpu[name, default: 0] += used
            footprint[name, default: 0] += memory
            count[name, default: 0] += 1
        }
    }
    previous = current
    for name in fixedCategories {
        cpuByCategory[name, default: []].append(cpu[name] ?? 0)
        footprintByCategory[name, default: []].append(footprint[name] ?? 0)
        countByCategory[name, default: []].append(count[name] ?? 0)
    }
    series.append(["second": second, "cpuPercent": cpu, "footprintMiB": footprint])
}

func round2(_ value: Double) -> Double { (value * 100).rounded() / 100 }
func percentile(_ values: [Double], _ fraction: Double) -> Double {
    let sorted = values.sorted()
    return sorted.isEmpty ? 0 : sorted[min(sorted.count - 1, Int(Double(sorted.count) * fraction))]
}
var summary: [String: Any] = [:]
for name in fixedCategories {
    let values = cpuByCategory[name] ?? [], memory = footprintByCategory[name] ?? []
    summary[name] = [
        "cpuMeanPercent": round2(values.reduce(0, +) / Double(max(values.count, 1))),
        "cpuP95Percent": round2(percentile(values, 0.95)),
        "footprintMedianMiB": round2(percentile(memory, 0.5)),
        "footprintMaxMiB": round2(memory.max() ?? 0),
        "processesMedian": percentile(countByCategory[name] ?? [], 0.5),
        "processesMax": (countByCategory[name] ?? []).max() ?? 0
    ]
}
let output: [String: Any] = ["seconds": seconds, "rules": rules.map { "\($0.category)=\($0.match)" },
                             "summary": summary, "processes": Array(seen.values), "series": series]
let data = try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys])
print(String(decoding: data, as: UTF8.self))
