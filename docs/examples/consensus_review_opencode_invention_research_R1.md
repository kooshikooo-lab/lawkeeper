# Worked example: consensus_review.py, science panel, round 1

Real first live test of `scripts/consensus_review.py`'s science panel,
2026-08-20 -- not a synthetic test case. Spec:
[consensus_case_opencode_invention_research.json](consensus_case_opencode_invention_research.json).

**Case:** opencode's Phase 1 research synthesis for Falcun's automated
invention-search feature (4 findings, each a claim about a real arXiv
preprint or a general literature synthesis). The spec, embedded here
rather than as a separate file (`docs/` holds only documentation --
found live by `validate_pre_commit.py` when a standalone `.json` spec
was first placed here):

```json
{
  "id": "opencode_invention_research",
  "title": "opencode's Phase 1 research synthesis for Falcun's automated invention-search feature",
  "context": "opencode (running headless, opencode/nemotron-3-ultra-free, in the falcun repo) was tasked with researching TRIZ+AI, recombinant innovation, and the Variance Paradox before designing a genome/fitness extension to Falcun's evolutionary core. It posted the summary below to the team-chat discussion as its Phase 1 output, before writing any Phase 2 design or code. This is a real test of consensus_review.py's science panel against real, freshly-produced research output -- not a synthetic test case.",
  "findings": [
    {
      "id": "F1",
      "title": "TRIZ-RAGNER (arXiv:2602.23656) method and results",
      "claim": "RAG framework for TRIZ contradiction mining from patents. 3-stage: (1) dense retrieval over TRIZ knowledge base (39 engineering parameters + PaTRIZ examples), (2) cross-encoder reranking, (3) structured LLM prompting for improving/worsening parameter extraction. Reports 84.2% F1 on PaTRIZ, +7.3pp over a GPT baseline.",
      "evidence": "opencode's own WebFetch of https://arxiv.org/abs/2602.23656 and https://arxiv.org/pdf/2602.23656 during this session."
    },
    {
      "id": "F2",
      "title": "CHIMERA (arXiv:2505.20779) scope and results",
      "claim": "A 28K+ recombination knowledge base mined from arXiv abstracts, distinguishing BLENDS (symmetric, intra-domain concept fusion) from INSPIRATIONS (directed, cross-domain analogies). Uses a fine-tuned Mistral-7B extractor (76% F1 on abstract classification, 94% generalization to biology).",
      "evidence": "opencode's own WebFetch of https://arxiv.org/abs/2505.20779 and https://arxiv.org/html/2505.20779v5 during this session."
    },
    {
      "id": "F3",
      "title": "The Variance Paradox (arXiv:2508.19264) core claim",
      "claim": "AI-assisted idea generation produces a U-shaped diversity dynamic: an initial decline in variance (via statistical optimization and epistemic deference to the model, the 'AI Prism' effect), with recombinant novelty recovering only under active human curation (the 'Paradoxical Bridge'). Passive/uncurated use is predicted to show a monotonic decline instead, which the paper treats as its own falsification condition.",
      "evidence": "opencode's own WebFetch of https://arxiv.org/abs/2508.19264 and https://arxiv.org/html/2508.19264v2 during this session."
    },
    {
      "id": "F4",
      "title": "Fleming-style recombinant innovation framing",
      "claim": "Invention modeled as recombinant search over a technology landscape (NK model): new combinations carry higher variance in outcome (more breakthroughs alongside more failures), component familiarity has a non-monotonic effect on outcome uncertainty, and citation counts serve as a fitness proxy for a combination's eventual value.",
      "evidence": "General literature synthesis, not a single fetched source -- flagged here specifically because it is the least directly-sourced of the four claims and is the one most worth checking for looseness."
    }
  ]
}
```

Save the block above as a `.json` file outside `docs/` (e.g. `consensus/specs/`) to actually run it.

**Result: 2/4 reviewers responded** -- reported honestly as "2/4," per
Law 23, not silently rounded up or treated as full consensus.
- `claude`: error -- claude CLI not authenticated in this subprocess
  context (known, logged in `BLOCKERS.md`).
- `nemotron-ultra`: responded. Verdict: **NEEDS REVISION**.
- `glm`: error -- OpenRouter 429, upstream shared-pool congestion (same
  class of failure `ai_review.py`'s retry-with-backoff already handles;
  this reviewer path doesn't yet reuse that helper -- worth doing).
- `gpt-oss`: responded. Verdict: **NEEDS REVISION**.

Both responding reviewers independently landed on the same verdict, for
concrete, specific reasons -- not generic pushback:
- No documented search methodology (search terms, inclusion criteria,
  screening logic) -- not reproducible as written.
- All 4 sources are unreviewed arXiv preprints; several precise metrics
  (84.2% F1, 76% F1, 94% cross-domain generalization) were stated as if
  settled rather than scrutinized. `nemotron-ultra` called the 94%
  generalization figure "particularly implausible without independent
  replication."
- F4 (the Fleming/NK-model recombinant-innovation framing) was the
  weakest of the four by both reviewers' independent judgment: no actual
  citation behind it, a general synthesis presented at the same
  confidence level as the three sourced findings.

This is real, substantive, non-generic critique produced by a real live
run -- the kind of information this tool was built to surface. It was
fed back to opencode via `team_chat.py` to actually change Phase 2's
design, not left to sit unread in a log (see Discussion #1,
kooshikooo-lab/falcun).

Full reviewer replies (regenerated, not committed -- see `.gitignore`'s
`consensus/` entry) live at
`consensus/case_opencode_invention_research/_replies_R1/` after running:

```
python scripts/consensus_review.py draft --spec consensus/specs/case.json --round 1 --panel science
python scripts/consensus_review.py run --spec consensus/specs/case.json --round 1 --panel science --approved
python scripts/consensus_review.py show --spec consensus/specs/case.json
```
