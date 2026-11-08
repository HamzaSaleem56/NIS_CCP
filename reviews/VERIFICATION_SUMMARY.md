# Independent Verification Summary

## Final technical verdict

**PASS AFTER REVIEW FIXES.** No independent reviewer found a blocking mathematical or cipher-implementation defect. The worked encryption example, inverse operations, Wilson intervals, success counts, candidate counts, and performance ratios were independently recomputed and matched. Submission readiness now depends only on normal operational checks: private-repository access for the instructor, confirmation of the group roster, and LMS upload before the deadline.

## Review panel

| Reviewer | Review outcome | Main verified points |
|---|---|---|
| GLM 5.3 | Cipher **PASS**; attacks **SOUND — approve** | Vigenère and Rail-Fence mathematics, inverse order, key-stream recovery, candidate ranking, no blocking correctness defect |
| GLM 5.3 Flash | Technical work complete; GitHub/ZIP were pending at review time | Requirement coverage, worked example, result-table/CSV consistency, honest short-ciphertext results |
| Claude Opus 5.5 | **PASS WITH FIXES**; no non-GitHub blocker | Worked example, Wilson intervals, performance ratios, complexity, all brief requirements |
| Claude Fable 5.1 | **PASS WITH FIXES**; no non-GitHub blocker | Numerical consistency, code/report alignment, deliverables and citation review |
| GPT 6 Astra | Core mathematics correct | Cipher stages, key-stream derivation, result claims and semantic API review |
| GPT 6.1 Sol Ultra | Core design/results accepted; publication was pending at review time | Requirement checklist, worked example, submission readiness and access considerations |
| Kimi verification | **8/8 tests pass; result checks pass** | 240 main attack trials, 80 prefix trials, raw-summary consistency, PDF/DOCX structure, comment-free source, ZIP integrity |

Individual review outputs are supplied alongside this summary.

## Findings applied to the project

- Removed every Python comment and docstring while preserving functionality; the final source has **zero comment tokens and zero docstrings**.
- Renamed the attack JSON field to `candidate_found` and documented that it is not a correctness guarantee.
- Removed tautological known-prefix checks and clarified that `m = L` relies on language ranking while `m > L` adds independent periodicity constraints.
- Restricted normalization to original ASCII letters so non-ASCII characters cannot enter through Unicode uppercase expansion.
- Enforced the documented 2–8 rail range even for empty input and CLI overrides.
- Added explicit UTF-8 corpus reads and normalized test inputs for Windows-compatible group reproduction.
- Corrected reference [2] to **D. Mukhopadhyay**.
- Documented weak/repetitive keys, equivalent-period keys, the IC shortlist recall limit, shorter effective periods, and timing noise.
- Made the performance-analysis paragraph dynamic from the actual benchmark CSV.
- Added the private GitHub URL, exact LMS steps, group-sharing instructions, and a roster reminder.

## Verified evidence

- Worked example: `MEETATTHELIBRARYATSIXPM` → `OVCITHZYEAPZTRPNTHYZXET` → `OTVZRCPPTIANETETXHYHZZY` using `CRYPTOGRAPHY` and seven rails.
- Frequency-only exact recovery: 0% at 100 characters, 35% at 200, 95% at 400, and 100% at 800/1,600/3,200 in the seeded 20-trial configurations.
- Known-prefix-24 exact recovery: 100% at every tested length in the same experiment.
- Main experiment: 240 trials; additional known-prefix experiment: 80 trials.
- Source: zero comments/docstrings; all eight tests pass after review fixes.
- Final report includes the repository URL and dynamically regenerated result/performance tables.
- Private GitHub repository is live on `main`: https://github.com/Global-Tech-hub/ccp-nis-fall-2026-vrfc.

## Remaining honest limitations

Statistical recovery is corpus- and configuration-dependent, not a universal guarantee. A repetitive key can satisfy minimum length while remaining weak. `candidate_found` means that an attack produced a candidate, not that the candidate is correct. Private GitHub access requires collaborator invitations. If this is a group submission, all member names and registration numbers must be added to the cover before LMS upload.
