# Independent Review — CT-486 CCP [CLO3] "Design and Break a Custom Cipher"

## VERDICT
**CONDITIONALLY READY — NOT SUBMITTABLE AS-IS.** Technical work is complete, internally consistent, and covers all four requirements (attacks exceed the "or" requirement — both implemented). However, one explicit deliverable (GitHub upload) and the final packaging/submission are outstanding per the packet's own verification notes. Resolve blockers before 8 Nov 2026.

## BLOCKERS
1. **GitHub upload missing — explicit assignment deliverable** ("Submit the code (uploaded to a GitHub repository)"). PLAN.md defers it to "owner approval" and README labels `GITHUB_UPLOAD.md` "optional" — the brief makes it **mandatory**. Repo must be live with the URL cited in the report/README before submission.
2. **Final submission package not assembled** — `verification.txt` itself states "GitHub URL and final group ZIP are pending."
3. **Group roster unconfirmed** — brief allows up to 04 members; packet names only one author (CR-23014). Confirm solo submission is permitted, or complete the roster/cover page in the report and ZIP.

## VERIFIED FINDINGS
- **Worked example independently recomputed — exact match.** Vigenère (key `CRYPTOGRAPHY`, 12 ≥ 10 chars) on `MEETATTHELIBRARYATSIXPM` → `OVCITHZYEAPZTRPNTHYZXET`; 7-rail rail-fence → `OTVZRCPPTIANETETXHYHZZY`. Both stages verified correct.
- **Design meets Req 1:** two distinct classical techniques (polyalphabetic substitution + transposition), two encryption stages, validated key ≥10.
- **README results table = `attack_summary.csv`** across all 12 rows (counts, %, CIs, timings). Wilson 95% CIs recomputed for 0/20 (16.11%), 7/20 (18.12–56.71), 19/20 (76.39–99.11), 20/20 (83.89 lower) — all correct.
- **Internal consistency:** 12 rows × 20 trials = 240 = "240 main attack trials"; 8 tests in log = README's claim; 16-page PDF = README's claim.
- **Req 3 met and exceeded:** both attacks implemented; success/effort documented over 6 lengths (100–3200): frequency 0%→100%, known-prefix 100%, timings 0.8–22.7 ms / 244–1685 ms.
- **Req 4 partially evidenced:** Shift baseline test passes (`test_shift_baseline ... ok`); asymptotic analysis and enc/dec benchmarks are **attested only** (report text and benchmark files not in this packet).
- **Honest reporting:** frequency attack's 0% at length 100 disclosed — no results inflation.
- **Attested, not independently verified** (files absent from packet): source code, tests, raw CSVs, report prose (security analysis, improvements, references, complexity, enc/dec performance metrics). `verification.txt` is self-reported evidence.

## DELIVERABLE / SUBMISSION CHECK

| Brief item | Status |
|---|---|
| Req 1: ≥2 classical techniques, 2 stages, key ≥10 | ✅ MET (verified) |
| Req 2: encrypt/decrypt program, A–Z, variable lengths | ✅ MET (round-trip tests pass; normalization documented) |
| Req 3: frequency + known-plaintext attacks | ✅ MET (both; exceeds "or") |
| Req 3: success rate + effort vs ciphertext lengths | ✅ MET (CSV, 20 trials/length, CIs, ms) |
| Req 4: complexity analysis (enc/dec) | ⚠️ ATTESTED (report claimed; not in packet) |
| Req 4: comparison to Shift cipher | ⚠️ PARTIAL (baseline test verified; comparison attested) |
| Del 1: algorithms + combination explanation | ⚠️ ATTESTED (PDF/DOCX valid; prose unchecked) |
| Del 2: attack program + documentation | ✅ MET |
| Del 3: report incl. security analysis, results, improvements, metrics | ⚠️ ATTESTED (13 tables/5 figures; enc/dec metrics not excerpted) |
| Del 3: **code on GitHub** | ❌ **MISSING — BLOCKER** |
| Final ZIP / submission | ❌ PENDING — BLOCKER |
| Group ≤4 / roster | ⚠️ VERIFY (1 member listed) |
| Deadline 8 Nov 2026 | ⚠️ Not yet submitted; schedule upload + packaging ahead |

**Minimum path to submission:** publish GitHub repo → insert URL, rebuild report → assemble ZIP with all `src/`, `tests/`, `results/`, report files → confirm roster → submit before deadline.
