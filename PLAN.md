# CCP NIS Fall 2026 — Execution Plan

## Assignment coverage

| Brief requirement | Planned evidence |
|---|---|
| Two or more classical techniques | Vigenère polyalphabetic substitution followed by Rail-Fence transposition |
| At least two encryption stages | Independent encrypt/decrypt functions and a worked stage-by-stage example |
| Key of at least 10 characters | Validated alphabetic key, minimum length 10; demonstrations use 12-character keys |
| Encryption and decryption for A–Z and variable lengths | Python CLI, normalization policy, unit tests for empty, short, and long inputs |
| Frequency-analysis attack | Rail-count enumeration, index-of-coincidence key-length analysis, chi-squared shift recovery, quadgram ranking |
| Known-plaintext attack | Partial-prefix key-stream recovery, candidate verification, full-message decryption |
| Attack success and effort at several lengths | Repeatable seeded experiments; CSV/JSON results and charts generated from actual runs |
| Time complexity and Shift-cipher comparison | Asymptotic analysis plus measured encryption/decryption/attack runtimes |
| Security improvements | Evidence-based limitations and low-complexity classical improvements; modern-security caveat |
| GitHub-ready code | README, source, tests, data attribution, reproducible experiment commands |

## Design: Vigenère–Rail-Fence Cascade (VRFC)

1. Normalize input to uppercase A–Z.
2. Stage I applies Vigenère substitution with a validated key of at least 10 letters.
3. Stage II applies Rail-Fence transposition. The rail count is deterministically derived from the same key in the range 2–8.
4. Decryption exactly reverses the order: undo Rail Fence, then undo Vigenère.
5. The attacker knows the algorithm and search bounds, but not the key (Kerckhoffs's principle).

## Work packages

1. Implement the cipher and both attacks using only the Python standard library.
2. Add unit tests and deterministic worked examples.
3. Train a character-quadgram scorer on included public-domain English text; use a separate text source for evaluation.
4. Measure attack success and runtime over multiple ciphertext lengths and repeated trials.
5. Produce a polished report with algorithms, mathematical model, diagrams, tables, actual results, limitations, and references.
6. Verify tests, reproduce the reported numbers, inspect the rendered PDF, and package the submission.

## Deliverables

- `report/CCP_NIS_Fall_2026_Report.pdf` — final submission report
- `report/CCP_NIS_Fall_2026_Report.docx` — editable report
- `src/` — cipher, attacks, benchmarks, and experiments
- `tests/` — automated tests
- `results/` — raw measurements and charts
- `README.md` — execution and reproduction guide

GitHub publication is required by the brief. The private repository is https://github.com/Global-Tech-hub/ccp-nis-fall-2026-vrfc; instructor/group access must be granted through collaborator invitations.
