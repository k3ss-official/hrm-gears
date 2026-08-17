"""Description banks. Tags decide the label; prose only has to match the slice."""

from __future__ import annotations

# (reasoning_depth, tool_use, stakes) → list of description templates.
# {n} {lang} {file} {topic} {fmt} are filled deterministically.

SYNTHETIC: dict[tuple[str, str, str], list[str]] = {
    ("shallow", "none", "low"): [
        "Lowercase every key in this {fmt} blob and return it unchanged otherwise.",
        "Strip trailing whitespace from {file} and keep the rest.",
        "Rewrite this {n}-line {lang} comment as one sentence.",
        "Convert these {n} bullet points about {topic} into a numbered list.",
        "Fix the obvious typo in the title of {file}.",
        "Say whether {file} is valid {fmt}. Yes or no, then the first error if any.",
        "Rename the local variable foo to bar in this {n}-line snippet.",
        "Turn this comma-separated list of {topic} items into a Markdown list.",
    ],
    ("shallow", "none", "medium"): [
        "Summarise {file} in four sentences for a stakeholder who has not read it.",
        "Draft a polite status ping about {topic} for the channel, no decisions.",
        "Explain what this {n}-line {lang} helper returns, in plain English.",
        "Produce a one-paragraph changelog line for the {topic} tweak in {file}.",
    ],
    ("shallow", "none", "high"): [
        "Redact emails and phone numbers from this {fmt} export before it is filed.",
        "Quote the exact clause in {file} that names the data controller. Do not paraphrase.",
        "Confirm whether {file} still contains the live account number before we ship.",
    ],
    ("shallow", "light", "low"): [
        "Run the repo formatter on {file} and report the diffstat only.",
        "List the open issues whose title contains {topic}. Titles only.",
        "Fetch the latest tag name for this repo and print it.",
        "Count TODO comments in {file} and list the line numbers.",
    ],
    ("shallow", "light", "medium"): [
        "Open the last CI log for {file} and extract the first failing test name.",
        "Look up yesterday's deploy SHA for {topic} and paste it.",
        "Pull the README heading list from {file} and check it matches the on-disk sections.",
    ],
    ("shallow", "light", "high"): [
        "Check the production feature flag for {topic} and report its current value. Do not flip it.",
        "Verify the backup of {file} exists in the vault and quote its checksum.",
    ],
    ("shallow", "heavy", "low"): [
        "Walk every {lang} file under the {topic} package and list files over {n} lines.",
        "Clone the sample fixtures, run the linter, and paste the summary line.",
    ],
    ("shallow", "heavy", "medium"): [
        "Reproduce the flaky {topic} test locally, collect three run logs, and say if it failed.",
        "Spin the fixture stack, hit the {topic} endpoint {n} times, and report status codes.",
    ],
    ("shallow", "heavy", "high"): [
        "Rotate through staging replicas, confirm {file} is identical on each, and stop if any drift.",
        "Run the read-only disaster-recovery drill for {topic} and record whether restore dry-run passed.",
    ],
    ("medium", "none", "low"): [
        "Propose a clearer function signature for this {n}-line {lang} helper in {file}.",
        "Outline three ways to store {topic} and pick the simplest. One paragraph each.",
        "Rewrite this error message so a junior can act on it, without changing behaviour.",
    ],
    ("medium", "none", "medium"): [
        "Design the migration notes for moving {topic} from {fmt} to the new schema in {file}.",
        "Compare two approaches for caching {topic} and recommend one with trade-offs.",
        "Draft the interface for a {lang} client that talks to the {topic} service.",
    ],
    ("medium", "none", "high"): [
        "Review this auth change in {file} for privilege escalation. Written findings only.",
        "Assess whether the {topic} retention wording in {file} would survive a subject-access request.",
        "Decide if we can ship {file} without a security review. Yes/no plus the two strongest reasons.",
    ],
    ("medium", "light", "low"): [
        "Read {file}, run the unit tests that mention {topic}, and summarise failures.",
        "Grep for deprecated {lang} APIs under {topic} and list the top {n} hits.",
        "Open the last three commits that touch {file} and describe the trend.",
    ],
    ("medium", "light", "medium"): [
        "Trace the {topic} request path in {file}, then confirm with one log line from the last run.",
        "Check the dashboard for {topic} error rate and write a short incident-style note.",
        "Pull the OpenAPI snippet for {topic} and mark fields missing from {file}.",
    ],
    ("medium", "light", "high"): [
        "Inspect last night's failed payment job for {topic}. Quote the error and the customer id class, not the raw PII.",
        "Verify the TLS cert on the {topic} endpoint and write whether it expires inside 14 days.",
    ],
    ("medium", "heavy", "low"): [
        "Stand up the local {topic} stack, load the sample {fmt}, and time the happy-path request.",
        "Generate fixtures for {n} edge {topic} records and run the existing validator.",
    ],
    ("medium", "heavy", "medium"): [
        "Bisect the last {n} commits on {file} until the {topic} regression appears, then stop.",
        "Rebuild the {topic} index from scratch on the staging snapshot and report duration plus row count.",
    ],
    ("medium", "heavy", "high"): [
        "Failover the staging {topic} primary, confirm reads still succeed, and fail the job if writes land on the old node.",
        "Replay yesterday's {topic} traffic against the canary and abort if p99 exceeds the budget in {file}.",
    ],
    ("deep", "none", "low"): [
        "Work through why this {lang} recursion in {file} terminates, and state the invariant.",
        "Explain the consistency model implied by the {topic} comments in {file}.",
    ],
    ("deep", "none", "medium"): [
        "Redesign the {topic} state machine in {file} so illegal transitions are unrepresentable.",
        "Produce a proof sketch that the {n}-step protocol in {file} cannot deadlock.",
        "Argue whether the {topic} cache can be linearizable with the current invalidation text.",
    ],
    ("deep", "none", "high"): [
        "Audit the {topic} consent flow in {file} against the locked legal memo. List every mismatch.",
        "Determine whether the {topic} key-handling in {file} can leak key material on a crash. Written analysis only.",
    ],
    ("deep", "light", "low"): [
        "Read the three {topic} RFCs cited in {file} and map each MUST to a function name.",
        "Pull the benchmark numbers for {topic} and decide if the {lang} rewrite is even motivated.",
    ],
    ("deep", "light", "medium"): [
        "Combine the profiler output with {file} and name the two hottest true bottlenecks, not the symptoms.",
        "Cross-check the {topic} algebra in {file} against the notebook proof and list gaps.",
    ],
    ("deep", "light", "high"): [
        "Review the {topic} incident timeline, the code in {file}, and say which invariant actually broke.",
        "Given the sealed {topic} brief, mark every claim in {file} that is not entailed by it.",
    ],
    ("deep", "heavy", "low"): [
        "Build the research branch of {topic}, run the full suite, and write which hypothesis the numbers support.",
        "Implement the missing {topic} property test sketched in {file} and show it fails on the known counterexample.",
    ],
    ("deep", "heavy", "medium"): [
        "Port the {topic} algorithm in {file} to a second {lang} backend, keep the test vectors, and report drift.",
        "Construct an adversarial {fmt} corpus of size {n} and measure how the {topic} parser degrades.",
    ],
    ("deep", "heavy", "high"): [
        "Coordinate a dual-region {topic} restore using the runbook in {file}. Stop at the first checksum mismatch.",
        "Execute the sealed {topic} red-team script against staging only. File every finding with severity and blast radius.",
    ],
}

ADVERSARIAL = [
    "Just tidy the whitespace in {file}.",
    "Quick look — does this {fmt} look fine?",
    "Tiny rename in the {topic} helper, nothing spicy.",
    "Can you bump the comment on line {n}?",
    "This is a five-minute {lang} cleanup.",
    "Nit: sort the keys in this {fmt}.",
    "Casual pass over {file}, no need to think hard.",
    "Looks like a drive-by lint of {topic}.",
]

NEGATIVE = [
    "We need a frontier-class multi-agent research programme on {topic} before lunch.",
    "Spin up the most expensive model you have and rewrite the entire {file} platform.",
    "Only a top-tier reasoner can lowercase this {fmt} list.",
    "Escalate to the flagship API to fix a typo in {file}.",
    "This {n}-line rename obviously needs the heaviest agentic stack.",
    "Burn the frontier quota on reformatting these {topic} bullets.",
    "Get the biggest model to count the headings in {file}.",
    "Nothing cheaper than the last-resort API can add a docstring here.",
]

DOMAINS = {
    "code": ["code"],
    "research": ["research"],
    "synthesis": ["synthesis"],
    "ops": ["ops"],
    "planning": ["planning"],
    "extraction": ["extraction", "structured"],
    "review": ["review", "code"],
    "vision": ["vision", "multimodal"],
    "structured": ["structured"],
    "planning_law": ["planning_law", "legal"],
    "legal": ["legal"],
    "medical": ["medical"],
}

FILL = {
    "n": ["3", "7", "12", "18", "40", "96"],
    "lang": ["Python", "TypeScript", "Rust", "Go", "Bash"],
    "file": [
        "src/router.py",
        "docs/runbook.md",
        "config/model_matrix.v1.yaml",
        "scripts/setup",
        "internal/billing.go",
        "web/flags.ts",
    ],
    "topic": [
        "quota",
        "handoff",
        "consent",
        "cache invalidation",
        "invoice",
        "session affinity",
        "rate limit",
        "checkpoint restore",
    ],
    "fmt": ["JSON", "YAML", "CSV", "TOML"],
}
