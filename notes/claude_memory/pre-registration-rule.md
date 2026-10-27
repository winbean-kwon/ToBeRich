---
name: pre-registration-rule
description: User-agreed rule — fix evaluation criteria before running experiments; never pick settings after seeing test/holdout results
metadata:
  type: feedback
---
Fix each experiment's selection rule and pass/fail criteria in the notebook/script (and commit) before running; report the pre-registered verdict even when it fails. Holdout 2026-07-14~10-26 already used once.

**Why:** the project's inflated results came from evaluation choices; user explicitly agreed not to cherry-pick, while still wanting a breakthrough.
**How to apply:** when proposing new experiments, state criteria up front; flag any post-hoc pattern as exploratory. Don't edit paper/ files directly (user has uncommitted edits) — write drafts as separate files. See [[project-state-2026-10-26]].
