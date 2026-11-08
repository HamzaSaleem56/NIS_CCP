## VERDICT

**PASS WITH FIXES.** The cryptography, code and statistics I could check are correct. One submission step is still open: the brief requires the code to be uploaded to GitHub, and that has not been done.

## BLOCKERS

1. **The code is not on GitHub yet, and no repository link appears anywhere.** The brief says "Submit the code (uploaded to a GitHub repository)". PLAN.md and README say publication is pending, and Report.md contains no repository URL. Once the owner approves, publish the repo, put the URL in the report (cover page or Appendix A, "GitHub-ready source" row) and in the README, regenerate the PDF and DOCX, and only then build the ZIP.

Nothing else blocks submission.

## VERIFIED FINDINGS

**Correct, checked by hand:**
- **Rail count for `CRYPTOGRAPHY`** (`src/cipher.py`, `derive_rails`): the weighted sum is 1118, and 1118 mod 7 = 5, so r = 7. This matches README, metadata and Report §4.
- **Stage I (Vigenère):** all 23 positions of `MEETATTHELIBRARYATSIXPM` produce `OVCITHZYEAPZTRPNTHYZXET`.
- **Stage II (Rail Fence, 7 rails, period 12):** the rows are OT, VZR, CPPT, IANE, TETX, HYHZ, ZY, which concatenate to `OTVZRCPPTIANETETXHYHZZY`. This matches the Report §4 table.
- **Inverses:** `rail_fence_decrypt` uses rail counts to split the ciphertext and then reads in zigzag order, which is exact. Vigenère is inverted by modular subtraction. Decryption order is reversed correctly in `decrypt`.
- **Wilson intervals** (`results/attack_summary.csv`): 0/20 gives (0, 16.11), 7/20 gives (18.12, 56.71), 19/20 gives (76.39, 99.11), and 20/20 gives (83.89, 100). All are correct.
- **Performance numbers** (`results/performance.csv`, Report §10.2): 445.80/225.89 = 1.97× and 548.40/259.98 = 2.11×. Throughput figures are consistent, for example 1000/0.5627 ms = 1.777 M chars/s.
- **Candidate count:** 56 = 7 rails × 8 shortlisted key lengths, matching `mean_candidates`.
- **Complexity table** (§10.1): it matches the code. The IC ranking is O(RMn), chi-squared is O(26n) per key length, and the known-prefix attack is O(Rn + RMm + RNn).

**Non-blocking fixes:**
1. **The "verification" steps in the known-prefix attack always pass** (`src/attack.py`, `known_plaintext_attack`).
   - `encrypt(candidate, key, rails) == normalized` is always true, because `candidate` was built by inverting exactly those stages.
   - `candidate[:len(known)] == known` is also guaranteed once the periodicity check has passed.
   - So Report §6.3 step 5 ("Verify consistency") overstates what the code does. Either remove these checks or describe them as sanity checks only. Removing them also saves O(n) per candidate.
2. **The m = L case is decided by the language model, not by algebra** (Report §6.3, §8.2; README "Recovers the full message when the known prefix is at least one key length long").
   - When the prefix length equals the key length (m = L), the periodicity test has no constraints. Every one of the 7 rails produces a candidate, and the quadgram score picks the winner.
   - The m = 12 result therefore relies on language ranking, not on a unique algebraic solution. Change "guaranteed" to "recoverable; unique when m > L".
3. **Normalization can let some non-ASCII characters through** (`src/cipher.py`, `normalize`). Uppercasing happens before filtering, so `'ß'` becomes `"SS"` and `'ı'` becomes `"I"`, and these survive. Report §2.1 says every non-A–Z character is removed. Either filter first (for example `ch.isascii()`) or soften the wording.
4. **The tests read the corpus without an explicit encoding** (`tests/test_cipher.py`, `read_text()` with no `encoding=`).
   - The tests compare `result.plaintext` with raw corpus slices, so they only pass because `evaluation_corpus.txt` is already normalized to A–Z. I inferred this from the passing tests.
   - Add `encoding='utf-8'` so group members on Windows can run them.
5. **Reference [2] has the wrong author name.** "D. Debdeep" should be "D. Mukhopadhyay".
6. **Not reviewed, because they were not supplied:** `experiment.py`, `build_report.py`, `make_diagrams.py`, the raw CSVs and the rendered PDF/DOCX. Claims such as "ten keys rotated" and the m = 12/48/96 prefix table are unverified. Before submitting, check that no literal `{{...}}` placeholder text is left in the PDF.
7. **Minor points:**
   - The frequency attack can return a doubled key (for example a 20-letter repeat of a 10-letter key). The plaintext is still exact, but the `key` field would not match the original.
   - Weak keys such as `AAAAAAAAAA` or `ABABABABAB` pass validation while having a short effective period. One sentence in §12 would cover this.

**Requirement coverage:** every part of the brief is covered.
- Two different classical stages (substitution + transposition)
- Key of at least 10 letters, enforced
- Encrypt/decrypt CLI that handles empty and long inputs
- Both a frequency attack and a known-plaintext attack, implemented
- Success rate and time at six message lengths
- O(n) analysis with a measured Shift-cipher comparison
- Improvements section
- Report sections matching the deliverables list

## DELIVERABLE/SUBMISSION CHECK

- **Ready:** source (`src/`), 8/8 tests passing (`results/verification.txt`), raw and summary results, charts, README, 16-page PDF, DOCX, and the requirement matrix (Appendix A).
- **Missing:** the GitHub URL (the blocker above). Also, the brief allows groups of up to 4 but README and the report list only one author. If this is a group submission, add every member's name and roll number to the report cover and the README.
- **Suggested order:**
  1. Apply fixes 1–5.
  2. Re-run the tests and `experiment.py` and confirm the numbers are unchanged.
  3. Publish the repo and insert the URL.
  4. Rebuild the PDF/DOCX and check for leftover placeholders.
  5. Build one ZIP containing the report PDF, the DOCX, `src/`, `tests/`, `data/`, `results/`, README and `SUBMISSION.txt` (the repo URL plus LMS steps: upload the PDF as the main file and the ZIP as an attachment, before the 8 Nov 2026 deadline).