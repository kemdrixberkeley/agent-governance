# agent-governance

A deterministic auditor that checks an autonomous agent fleet against its own rules, every night, without a human in the loop.

## The problem

I run a fleet of AI agents that execute unattended: they read mail, browse, fill forms, publish and report. Within weeks I had the problem everyone running agents eventually gets.

The rules grew to 128 written norms across two files. Agents skipped them silently. Nothing broke loudly, quality just drifted: a claim asserted without checking, a step reported as done that was only attempted, a rule that existed on paper and had never once been applied.

Prose does not enforce anything. It is aspiration with good grammar.

## The approach

Every rule that can be expressed as a machine check moves out of the rulebook and into the auditor. What stays in prose is only what genuinely needs judgement.

The auditor runs after the fleet and outputs either a list of concrete failures, naming the run and the rule, or the single word `LIMPIO`.

It currently enforces **37 dimensions**, among them:

- **Phantom rules.** Every rule ID cited in an agent prompt must exist in the rulebook. Agents hallucinate rule numbers.
- **Orphan rules.** Every rule in the rulebook must be either read or explicitly excluded by at least one agent. A rule nobody reads is dead weight that dilutes the ones that matter.
- **Evidence line.** Each run's journal entry must close with a structured line proving four checks were performed: currency re-verified, blocking question asked, next reversible step already executed, unrequested strategic read given.
- **Dead runs.** A task can be marked executed by the scheduler and still have done nothing. The proof that a run happened is that it wrote to the journal, not that the platform says it fired.
- **Success asserted without observation.** Any success flag computed from the absence of something, rather than the presence of evidence, is a defect. This one was added after a command reported `published: true` while reading back the text still sitting in the compose box.
- **Repealed text surviving in a prompt.** The rulebook is authoritative, but the prompt is what executes. A rule corrected only in the rulebook is a rule corrected halfway.
- **Suspended capability with no review date.** A pause with no date is a permanent removal wearing a temporary label.
- **Cross-file consistency**, numbering collisions, stale entries, and drift between prompts and the rulebook.

## Why this matters more than it looks

The interesting failure mode of autonomous agents is not that they break. It is that they quietly stop doing the parts nobody measures, while still reporting success. A nightly deterministic check is the cheapest defence I have found, and it costs a few seconds per run.

Every rule here was born from a real incident, not from a checklist someone imagined. The list grows because production keeps teaching, and it will keep growing.

## Running it

```bash
python3 auditor.py
```

Output is either `LIMPIO: N dimensiones` or a numbered list of failures. Paths are placeholders (`<WORKSPACE>`); point them at your own rulebook, prompts and journal.

## Design notes

- **No dependencies.** Standard library only, so it can run inside any agent's own environment.
- **Fails loudly, fixes nothing.** The auditor reports; a separate agent repairs. Mixing the two hides problems.
- **Negative tests are mandatory.** Every check is proven by deliberately breaking the thing it guards and confirming the auditor catches it. A check that has never failed has never been tested.
- **A detector that cries wolf gets ignored.** Two checks here were rewritten after firing on correct work. A false alarm is not a harmless cost, it is how a useful check dies.

## Status

Running nightly in production against a live fleet. The version in this repo is a snapshot; the dimension count moves as incidents arrive.
