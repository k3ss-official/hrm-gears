let meta = #{
    name: "routing-data-v1",
    description: "Generate and gate MVP routing JSONL. No trainer. No weights.",
    when_to_use: "Need publishable data/routing/v1 examples gated against the matrix",
    phases: [
        #{ title: "Generate", detail: "run frozen-policy generator" },
        #{ title: "Skeptics", detail: "independent schema, priority, mix checks" },
        #{ title: "Coverage", detail: "strict validate.py gates" },
        #{ title: "Report", detail: "write README if gates pass" },
    ],
};

let verdict_schema = #{
    "type": "object",
    "required": ["pass", "errors", "notes"],
    "properties": #{
        "pass": #{ "type": "boolean" },
        "errors": #{ "type": "integer" },
        "notes": #{ "type": "string" },
    },
};

let repo = if args == () { "/Volumes/hermes/play/hrm-gears" } else if args.repo == () { "/Volumes/hermes/play/hrm-gears" } else { args.repo };
let n = if args == () { 3000 } else if args.n == () { 3000 } else { args.n };

phase("Generate");
let gprompt = "";
gprompt += "You are in the hrm-gears repo at " + repo + ". ";
gprompt += "Run the frozen-policy generator. Do NOT implement a trainer, routing head, or flywheel. ";
gprompt += "Do NOT edit ./setup, scripts/setup, or the README install hero. ";
gprompt += "Do NOT invent model ids. Command: ";
gprompt += ".venv/bin/python scripts/routing_data/generate.py --n " + n.to_string();
gprompt += " Then run: .venv/bin/python scripts/routing_data/validate.py --strict --write-readme";
gprompt += " Report exit codes and the printed totals. If generate is already on disk and validate --strict exits 0, that is success.";
let gen = agent(gprompt, #{
    label: "generate",
    capability_mode: "execute",
    output_schema: verdict_schema,
});
if gen == () || !gen.success || gen.output.pass != true {
    complete(#{ summary: "generate/validate failed", pass: false });
}

phase("Skeptics");
let jobs = [];
jobs.push(#{
    prompt: "Repo " + repo + ". Independently verify schema of data/routing/v1. Read scripts/routing_data/validate.py REQUIRED fields and check 25 lines from train.jsonl and 10 from held_out.jsonl with read_file. Count missing keys, bad enums, non-null outcome, unknown model ids vs config/model_matrix.v1.yaml. Do not trust the generator. pass=true only if you inspected lines and found 0 schema breaks. errors=count. notes=short.",
    label: "skeptic-schema",
    capability_mode: "read-only",
    output_schema: verdict_schema,
});
jobs.push(#{
    prompt: "Repo " + repo + ". Independently re-derive chosen_model for 20 train.jsonl lines using scripts/routing_data/policy.py rules (free then non_frontier_sub then frontier_sub then non_frontier_api then frontier_api; YAML order inside a tier; escalating domains vision/medical=3, planning_law/legal=2). Read policy.py and the 20 lines. pass=true only if every line's chosen_model matches the policy winner. errors=mismatches. notes=short.",
    label: "skeptic-priority",
    capability_mode: "read-only",
    output_schema: verdict_schema,
});
jobs.push(#{
    prompt: "Repo " + repo + ". Check mix and leakage. Count label_source in train+held_out (you may run wc and a short python one-liner). Need ~15% adversarial, >=5% negative, rest synthetic. held_out descriptions must not appear in train. pass=true only if mix and leakage hold. errors=0 if ok. notes=percentages.",
    label: "skeptic-mix",
    capability_mode: "execute",
    output_schema: verdict_schema,
});
let skeptics = parallel(jobs);
let skeptic_fail = 0;
for s in skeptics {
    if s == () || !s.success || s.output.pass != true {
        skeptic_fail += 1;
    }
}

phase("Coverage");
let cprompt = "";
cprompt += "Repo " + repo + ". Run .venv/bin/python scripts/routing_data/validate.py --strict --write-readme . ";
cprompt += "pass=true only if the process exits 0 and printed pass: true. ";
cprompt += "errors=number of failed gates (0-3). notes=copy the totals and gate booleans.";
let cov = agent(cprompt, #{
    label: "coverage",
    capability_mode: "execute",
    output_schema: verdict_schema,
});

phase("Report");
let ok = skeptic_fail == 0 && cov != () && cov.success && cov.output.pass == true;
let summary = "routing-data-v1 skeptics_failed=" + skeptic_fail.to_string();
if ok {
    summary = "routing-data-v1 PASS files=data/routing/v1/{train,held_out,README}.jsonl";
}
complete(#{
    summary: summary,
    pass: ok,
    skeptic_fail: skeptic_fail,
    coverage_pass: cov != () && cov.success && cov.output.pass == true,
});
