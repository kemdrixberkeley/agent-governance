# agent-governance

A deterministic auditor that checks an autonomous agent fleet against its own rules, every night, without a human in the loop.

## The problem

I run a fleet of AI agents that execute unattended: they read mail, browse, fill forms, publish and report. Within weeks I had the problem everyone running agents eventually gets.

The rules grew to 139 written norms across two files. Agents skipped them silently. Nothing broke loudly, quality just drifted: a claim asserted without checking, a step reported as done that was only attempted, a rule that existed on paper and had never once been applied.

Prose does not enforce anything. It is aspiration with good grammar.

## The approach

Every rule that can be expressed as a machine check moves out of the rulebook and into the auditor. What stays in prose is only what genuinely needs judgement.

The auditor runs after the fleet and outputs either a list of concrete failures, naming the run and the rule, or the single word `LIMPIO`.

It currently enforces 20 dimensions, among them:

- **Phantom rules.** Every rule ID cited in an agent prompt must exist in the rulebook. Agents hallucinate rule numbers.
- **Orphan rules.** Every rule in the rulebook must be either read or explicitly excluded by at least one agent. A rule nobody reads is dead weight that dilutes the ones that matter.
- **Evidence line.** Each run's journal entry must close with a structured line proving four checks were performed: currency re-verified, blocking question asked, next reversible step already executed, unrequested strategic read given.
- **Cross-file consistency.** State files, journal and the outside world must agree. A record saying "sent" with no delivery confirmation fails.
- **Numbering collisions**, stale entries, and drift between prompts and the rulebook.

## Why this matters more than it looks

The interesting failure mode of autonomous agents is not that they break. It is that they quietly stop doing the parts nobody measures, while still reporting success. A nightly deterministic check is the cheapest defence I have found, and it costs a few seconds per run.

Every rule added here was born from a real incident, not from a checklist someone imagined.

## Running it

```bash
python3 auditor.py
```

Exit output is either `LIMPIO: 20 dimensiones` or a numbered list of failures. Paths are placeholders (`<WORKSPACE>`); point them at your own rulebook, prompts and journal.

## Design notes

- **No dependencies.** Standard library only, so it can run inside any agent's own environment.
- **Fails loudly, fixes nothing.** The auditor reports; a separate agent repairs. Mixing the two hides problems.
- **Negative tests are mandatory.** Every check is proven by deliberately breaking the thing it guards and confirming the auditor catches it. A check that has never failed has never been tested.
