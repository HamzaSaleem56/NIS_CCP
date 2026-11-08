# VRFC — Design and Break a Custom Cipher

**Course:** Network and Information Security (CT-486)  
**Assessment:** Complex Computing Problem, CLO3, Fall 2026  
**Author:** Muhammad Imaad Tahir (CR-23014)  
**GitHub:** https://github.com/HamzaSaleem56/NIS_CCP (public)

VRFC (Vigenère–Rail-Fence Cascade) is a two-stage classical cipher with a complete Python implementation and two cryptanalysis methods. It is an educational project, not production cryptography.

## Design

1. Normalize input to uppercase A–Z.
2. Apply repeating-key Vigenère substitution with a validated key of at least 10 letters.
3. Derive a rail count in 2…8 from that key.
4. Apply Rail-Fence transposition.
5. Decrypt in reverse order: undo Rail Fence, then undo Vigenère.

Worked example:

```text
Plaintext:  MEETATTHELIBRARYATSIXPM
Key:        CRYPTOGRAPHY
Rails:      7
Stage I:    OVCITHZYEAPZTRPNTHYZXET
Ciphertext: OTVZRCPPTIANETETXHYHZZY
Decrypted:  MEETATTHELIBRARYATSIXPM
```

## Requirements

- Python 3.10 or newer for the cipher, attacks, tests, and experiments.
- No third-party package is required for the core cipher or attacks.
- Report/chart regeneration uses `requirements-report.txt` and Linux DejaVu/Liberation fonts.

## Encrypt and decrypt

Run from the project root:

```bash
python3 src/cipher.py encrypt --key CRYPTOGRAPHY --text "MEET AT THE LIBRARY AT SIX PM"
python3 src/cipher.py decrypt --key CRYPTOGRAPHY --text OTVZRCPPTIANETETXHYHZZY
python3 src/cipher.py rails --key CRYPTOGRAPHY
```

Use `--input path.txt` instead of `--text` for file input. Decryption recovers the normalized A–Z plaintext; punctuation and spacing are deliberately removed during normalization.

## Attack simulations

### Frequency-only attack

Enumerates rail counts 2…8, ranks key lengths through 20 using the index of coincidence, recovers shifts with chi-squared analysis, and reranks 56 candidates with an English quadgram model. Shorter effective periods are allowed because a divisor of the true period can decrypt correctly. The top-eight IC shortlist bounds cost but can miss the true period on short or noisy text.

```bash
python3 src/attack.py frequency --cipher-file ciphertext.txt
```

### Partial-known-plaintext attack

Attempts full-message recovery when the known prefix is at least one key length long. Prefixes longer than the key provide stronger periodicity filtering; at the exact key-length boundary, language ranking plays a larger selection role:

```bash
python3 src/attack.py known --known-prefix MEETATTHELIBRARYATSIXPM --cipher-file ciphertext.txt
```

Both commands emit JSON containing the candidate plaintext, key, rails, language score, candidate count, and elapsed milliseconds. The JSON `candidate_found` field means a candidate was found; it is not a correctness claim. Exact recovery is evaluated separately against ground truth by the experiment.

## Tests and reproducible experiments

```bash
python3 -m unittest discover -s tests -v
python3 src/experiment.py --trials 20 --seed 20261108
```

The suite has 8 tests covering a standard Vigenère vector, Rail-Fence and VRFC round trips, boundary lengths, key validation, Shift baseline behavior, and both known-prefix and frequency-only recovery.

The experiment writes raw per-trial data, aggregate statistics, Wilson intervals, benchmarks, and charts under `results/`. Training and evaluation use different public-domain texts; see `data/SOURCES.md`.

## Verified headline results

Twenty trials per length, seed `20261108`:

| Ciphertext length | Frequency-only exact recovery | 24-letter known-prefix exact recovery |
|---|---|---|
| 100 | 0/20 (0%) | 20/20 (100%) |
| 200 | 7/20 (35%) | 20/20 (100%) |
| 400 | 19/20 (95%) | 20/20 (100%) |
| 800 | 20/20 (100%) | 20/20 (100%) |
| 1,600 | 20/20 (100%) | 20/20 (100%) |
| 3,200 | 20/20 (100%) | 20/20 (100%) |

These are measured outcomes for the included corpus, keys, and attack bounds—not universal guarantees. See the report for confidence intervals, mean letter accuracy, timings, complexity, and limitations.

## Final report

- `report/CCP_NIS_Fall_2026_Report.pdf` — 16-page submission report
- `report/CCP_NIS_Fall_2026_Report.docx` — editable version
- `report/Report.md` — source with dynamic result-table placeholders

To regenerate after installing report dependencies:

```bash
python3 -m pip install -r requirements-report.txt
python3 src/make_diagrams.py
python3 src/build_report.py
```

## Project structure

```text
src/                 Cipher, attacks, experiments, diagrams, report builder
tests/               Automated unit and recovery tests
data/                Training/evaluation corpora and attribution
results/             Raw CSVs, aggregate results, metadata, charts
report/              Final PDF, DOCX, and report source
```

## Security notice

The small rail space is enumerable, Vigenère periodicity is statistically recoverable, and a one-key-length known prefix exposes every key-stream position. Length validation does not guarantee entropy: repetitive keys such as `AAAAAAAAAA` are weak despite satisfying the minimum length. Do not use VRFC for real sensitive data. Use a maintained authenticated-encryption library for production systems.
