# VERDICT

**PASS WITH FIXES** — technical content, numbers, and code are internally consistent and verified by hand; the only genuine blocker is the unmet GitHub-upload requirement.

# BLOCKERS

1. **GitHub repository not published / no URL in the submission.** Brief deliverable 3 states "Submit the code (uploaded to a GitHub repository)". Neither `README.md`, `Report.md` (Appendix A says only "GitHub-ready source"), nor the PDF contains a repository URL. Publish the repo, then insert the URL in README and the report (Appendix A / §5) and re-render PDF/DOCX before submitting.

# VERIFIED FINDINGS

**Recomputed by hand — correct**
- Worked example (`README.md`, `Report.md §4`, `results/experiment_metadata.json`): `derive_rails("CRYPTOGRAPHY")` weighted sum = 1118, 1118 mod 7 = 5 → 7 rails ✓. All 23 Vigenère shifts give `OVCITHZYEAPZTRPNTHYZXET` ✓. Zigzag with period 12 yields rows `OT/VZR/CPPT/IANE/TETX/HYHZ/ZY` → `OTVZRCPPTIANETETXHYHZZY` ✓.
- Standard vector `ATTACKATDAWN`/`LEMON` → `LXFOPVEFRNHR` ✓ (`tests/test_cipher.py`).
- Wilson 95% intervals in `results/attack_summary.csv`: 0/20 → [0, 16.11], 7/20 → [18.12, 56.71], 19/20 → [76.39, 99.11], 20/20 → [83.89, 100] — all recomputed ✓.
- Headline percentages identical across README table, executive summary, §8.1, and CSV ✓. §8.1 "63.15%" letter accuracy ✓. "≈8 observations per column" at 100/12 ✓.
- §10.2 ratios: 445.8021/225.893 = 1.97×, 548.402/259.9768 = 2.11× ✓; `million_chars_per_sec` column matches `input_length/median_ms` ✓.
- Candidate count 56 = 7 rails × `ic_shortlist=8` matches `attack.py` and CSV `mean_candidates` ✓. `verification.txt` 240 = 12 rows × 20; 80 = 4 prefix lengths × 20 ✓.
- Code↔report consistency: rail formula §2.3, zigzag rule §2.4, key-length loop `10…min(20,m)` §6.3, IC ranking of 1…20 §6.2, benchmark repeats 21/7 §7 — all match source and CSVs ✓.
- Complexity expressions §10.1 are consistent with the loops in `frequency_attack` / `known_plaintext_attack` ✓.

**Accuracy issues (fix, non-blocking)**
- `src/attack.py` `known_plaintext_attack`: both "consistency" checks are tautologies. Given the periodicity filter, `candidate[:len(known)] == known` always holds, and `encrypt(candidate, key, rails)` always equals `normalized` because it just re-applies the inverse. Report §6.3 step 5 ("Verify consistency and select…") therefore describes a filter that can never reject; selection is purely by quadgram score. Results unaffected; reword the step (e.g. "re-encryption sanity check") or drop the claim.
- `Report.md` reference [2]: "D. Debdeep" — author is Debdeep **Mukhopadhyay** (IIT Kharagpur); should be "D. Mukhopadhyay". Reference [4] (EPFL Graph Search) is a weak secondary source for Kerckhoffs; prefer Kerckhoffs (1883) or Stallings [1].

**Minor / informational**
- `test_known_prefix_recovers_full_message` and `test_frequency_attack_recovers_long_message` compare `result.plaintext` to a *raw* corpus slice; they pass (per `verification.txt`) only because `data/evaluation_corpus.txt` is pre-normalized single-line A–Z. Fragile but not wrong.
- Leftovers after docstring removal: `ArgumentParser(description=__doc__)` now resolves to `None` in both CLIs (harmless); `decrypt` imported but unused in `attack.py`.
- Timing noise: frequency attack at 800 chars (578.7/527.5 ms) is faster than at 400 (636.7/578.8 ms); `shift_encrypt@100k` (43.17 ms) slower than `vigenere_encrypt@100k` (35.83 ms). §7/§10.2 already caveat the environment; one sentence acknowledging noise would pre-empt a grader's question.
- `PLAN.md` lists the PDF at project root; README places it under `report/`. Harmless internal inconsistency.
- Not supplied in packet, accepted on `verification.txt` only: `src/experiment.py`, raw CSVs, `known_prefix_lengths.csv`, `data/SOURCES.md`, `GITHUB_UPLOAD.md`, `requirements-report.txt`, the "600,000 letters" training size, and "ten different keys" claim.

# DELIVERABLE/SUBMISSION CHECK

| Brief item | Status |
|---|---|
| Two classical techniques, ≥2 stages | ✓ Vigenère + Rail Fence (§2–4, `cipher.py`) |
| Key ≥ 10 characters | ✓ `validate_key`, 12-letter demo key |
| Encrypt/decrypt program, A–Z, variable lengths | ✓ CLI + round-trip tests 0…1001 chars |
| Frequency-analysis attack | ✓ rails × IC × χ² × quadgram |
| Known-plaintext attack | ✓ prefix key-stream recovery |
| Success rate + effort at various lengths | ✓ 6 lengths × 20 trials, times, candidate counts, Wilson CIs |
| Time complexity + Shift comparison | ✓ §10 table + 4 input sizes |
| Security analysis + improvements | ✓ §9, §11 |
| Performance metrics | ✓ §8, §10, `performance.csv` |
| Report (PDF/DOCX) | ✓ 16 A4 pages, 8/8 tests per `verification.txt` |
| **Code on GitHub** | **✗ pending — blocker above** |
| Group members / roll numbers on title page | ⚠ unverified — README lists one author (CR-23014); brief allows up to 4. Confirm the rendered title page before submission. |
| Final ZIP + LMS instructions | ⚠ not in packet; produce after GitHub URL is inserted so the ZIP'd report matches the published one. |

Recommended order: fix [2] citation + §6.3 wording → publish repo → insert URL → rebuild PDF/DOCX → confirm title page → build ZIP → submit (deadline 8 Nov 2026).