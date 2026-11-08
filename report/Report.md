# Executive summary

This project presents **VHC (Vigenère–Hill Cascade)**, a two-stage classical product cipher built from two ciphers covered in the course lectures. Stage I applies a repeating-key **Vigenère** substitution with a validated key of at least 10 letters. Stage II passes the result through a **2×2 Hill cipher**, which encrypts letters in pairs with an invertible key matrix. The two stages use independent secrets: the Vigenère keyword and a 4-letter Hill key. The reference example uses the 12-letter Vigenère key `CRYPTOGRAPHY` and the Hill key `HILL`.

The submission includes a standard-library Python implementation, exact decryption for every message length, automated tests, a ciphertext-only frequency-analysis attack, and a partial-known-plaintext attack. The analysis shows that the cascade collapses algebraically into a Hill cipher with a repeating offset. The frequency attack exploits this: it recovers each row of the inverse Hill matrix with the index of coincidence (IC), recovers the Vigenère shifts with chi-squared frequency analysis, and ranks complete candidates with an English quadgram model. The known-plaintext attack cancels the Vigenère offsets by subtracting blocks, solves for the Hill matrix with modular linear algebra, and then decrypts the full message.

All reported measurements are outputs of the included reproducible experiment, not estimated values. Across 20 independent trials per length, the frequency-only attack achieved exact full-message recovery in **0% of 100-character cases, 30% at 200 characters, 85% at 400 characters, and 100% at 800, 1,600, and 3,200 characters**. With a 32-character known prefix, exact recovery was **100% at every tested length**, in under 3 ms. These results show that adding a Hill stage hides single-letter patterns but does not make a repeating-key classical cipher secure.

> Security scope: VHC is an educational construction for classical cryptanalysis. It must not be used to protect real credentials, patient data, financial information, or production communications.

# 1. Introduction and objectives

Classical ciphers are useful teaching systems because their operations are transparent and their weaknesses can be measured directly. A **monoalphabetic or polyalphabetic substitution** such as Vigenère replaces each letter on its own. A **polygraphic substitution** such as Hill replaces whole blocks of letters at once, so one ciphertext letter depends on several plaintext letters. Combining the two produces a small **product cipher**: the output of one classical transformation becomes the input to another.

Both stages come from the course material: the Vigenère cipher (Lecture 3) and the Hill cipher (Lecture 7). The objective is not merely to produce unreadable text. A complete design must also be reversible, testable, and breakable under an explicit attacker model. Accordingly, this project has four technical objectives:

- implement a correct two-stage cipher for arbitrary-length A–Z messages;
- use a validated encryption key of at least 10 characters;
- demonstrate both statistical and known-plaintext cryptanalysis with measured outcomes; and
- quantify asymptotic and practical cost relative to a single Shift cipher.

The work follows Kerckhoffs's principle: the attacker knows the algorithm, implementation, and configured search bounds; only the keys and plaintext are secret [4]. This is a stronger and more realistic assumption than relying on concealment of the algorithm.

# 2. Cipher design

## 2.1 Notation and data domain

| Symbol | Meaning |
|---|---|
| P | Normalized plaintext, P ∈ {A,…,Z}ⁿ |
| C | Final ciphertext, C ∈ {A,…,Z}ⁿ |
| K | Vigenère keyword of length L ≥ 10 |
| kᵢ | Numeric shift of key letter i, in 0…25 |
| T | Intermediate Vigenère ciphertext |
| H | 2×2 Hill key matrix built from a 4-letter Hill key |
| n | Number of normalized characters |

Input is uppercased and every non-ASCII-A–Z character is removed. Thus `Meet at 6 PM!` becomes `MEETATPM`, and letters map to numbers A = 0, …, Z = 25. This convention makes the alphabet, indexing, and frequency model unambiguous. Decryption recovers the exact **normalized** plaintext; spaces and punctuation are intentionally outside the cipher domain. Empty strings, one-character messages, odd lengths, and long inputs are all supported, and the ciphertext always has the same length as the plaintext.

## 2.2 Stage I — Vigenère substitution

For plaintext position i and key length L, Stage I computes:

> Tᵢ = (Pᵢ + kᵢ mod L) mod 26

The inverse operation is:

> Pᵢ = (Tᵢ − kᵢ mod L) mod 26

A repeating keyword makes this polyalphabetic: the same plaintext letter can map to different ciphertext letters at different positions. Unlike a single Shift cipher, however, the repeated key creates periodic structure that an attacker can exploit [1], [2]. The implementation rejects any keyword with fewer than 10 letters.

## 2.3 Stage II — 2×2 Hill cipher

The 4-letter Hill key h₀h₁h₂h₃ fills a 2×2 matrix row by row:

> H = [[h₀, h₁], [h₂, h₃]]

Stage II splits T into pairs (t₁, t₂) and treats each pair as a column vector [3]:

> (c₁, c₂)ᵀ = H · (t₁, t₂)ᵀ mod 26

Decryption needs the inverse matrix, which exists only when det(H) shares no factor with 26, meaning the determinant must be odd and not 13. The implementation checks this and rejects keys such as `AAAA` (det 0) or `ABCD` (det 24). The inverse is:

> H⁻¹ = det(H)⁻¹ · [[h₃, −h₁], [−h₂, h₀]] mod 26

Of the 26⁴ = 456,976 possible matrices, 157,248 are invertible mod 26, so the Hill stage on its own has 157,248 possible keys.

**Odd lengths.** The Hill stage needs pairs. When n is odd, the final letter is left out of the Hill stage and is protected by the Vigenère stage only. This keeps decryption exact and the ciphertext the same length as the plaintext, with no padding letters to remove.

![Figure 1. VHC encryption architecture.](../results/cipher_architecture.png)

The final construction is:

> C = Hill(H, Vigenère(K, P))

Decryption must invert the stages in reverse order:

> P = Vigenère⁻¹(K, Hill⁻¹(H, C))

## 2.4 How the stages combine

Write the plaintext as pairs Pⱼ = (P₂ⱼ, P₂ⱼ₊₁) and the matching key pairs as kⱼ = (k₂ⱼ mod L, k₂ⱼ₊₁ mod L). Then each ciphertext pair is:

> Cⱼ = H · (Pⱼ + kⱼ) = H · Pⱼ + wⱼ, where wⱼ = H · kⱼ

The key pairs repeat every Π = L / gcd(L, 2) pairs: Π = L/2 when L is even and Π = L when L is odd. So the cascade is exactly a **Hill cipher with a repeating offset vector**: one fixed matrix H plus Π offset vectors. This equation is the basis of both the security analysis and both attacks. It shows the stages do work together, since every ciphertext letter now depends on two plaintext letters and two key letters, but it also shows the structure an attacker can exploit.

# 3. Algorithms and correctness

## 3.1 Encryption algorithm

```text
ALGORITHM VHC-Encrypt(P, K, HK)
1  P ← uppercase A-Z letters of P; K ← uppercase A-Z letters of K
2  require |K| ≥ 10 and |HK| = 4
3  H ← [[HK0, HK1], [HK2, HK3]]; require gcd(det H mod 26, 26) = 1
4  for i ← 0 to |P| − 1:
5      T[i] ← (P[i] + K[i mod |K|]) mod 26
6  for j ← 0 to ⌊|T| / 2⌋ − 1:
7      (C[2j], C[2j+1]) ← H · (T[2j], T[2j+1]) mod 26
8  if |T| is odd: C[|T| − 1] ← T[|T| − 1]
9  return C
```

## 3.2 Decryption algorithm

```text
ALGORITHM VHC-Decrypt(C, K, HK)
1  C ← uppercase A-Z letters of C; K ← uppercase A-Z letters of K
2  require |K| ≥ 10 and |HK| = 4
3  H ← [[HK0, HK1], [HK2, HK3]]; H⁻¹ ← det(H)⁻¹ · adj(H) mod 26
4  for j ← 0 to ⌊|C| / 2⌋ − 1:
5      (T[2j], T[2j+1]) ← H⁻¹ · (C[2j], C[2j+1]) mod 26
6  if |C| is odd: T[|C| − 1] ← C[|C| − 1]
7  for i ← 0 to |T| − 1:
8      P[i] ← (T[i] − K[i mod |K|]) mod 26
9  return P
```

## 3.3 Why decryption is exact

Key validation guarantees that H is invertible mod 26, so H⁻¹ · H = I and Step 5 restores every Stage I pair exactly. An odd final letter never enters the Hill stage, so it passes through unchanged. Modular subtraction then reverses each modular addition of Stage I. Therefore `Decrypt(Encrypt(P, K, HK), K, HK) = P` for every normalized P, every valid keyword K, and every valid Hill key HK. The automated suite checks this for lengths 0–79 under four Hill keys, for boundary lengths up to 1,001 characters, and for the textbook Hill example (`SHORTEXAMPLE` with key `HILL` gives `APADJTFTWLFJ`).

# 4. Worked example

The example uses the normalized plaintext `MEETATTHELIBRARYATSIXPM` (23 letters), the 12-character Vigenère key `CRYPTOGRAPHY`, and the Hill key `HILL`.

| Step | Value |
|---|---|
| Plaintext P | MEETATTHELIBRARYATSIXPM |
| Vigenère key K | CRYPTOGRAPHY |
| Hill key / matrix H | HILL → [[7, 8], [11, 11]], det = 15 |
| Inverse matrix H⁻¹ | [[25, 22], [1, 23]] |
| Stage I output T | OVCITHZYEAPZTRPNTHYZXET |
| Final ciphertext C | GVAGHADTCSTYJGBWHAETLLT |
| Decrypted output | MEETATTHELIBRARYATSIXPM |

Stage II works pair by pair. For the first pair, `OV` = (14, 21):

> c₁ = 7·14 + 8·21 = 266 ≡ 6 (G), c₂ = 11·14 + 11·21 = 385 ≡ 21 (V)

| Stage I pairs T | OV | CI | TH | ZY | EA | PZ | TR | PN | TH | YZ | XE | T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ciphertext pairs C | GV | AG | HA | DT | CS | TY | JG | BW | HA | ET | LL | T |

The 23rd letter `T` has no partner, so it carries only its Vigenère shift. The example also shows the weakness from Section 2.4: with L = 12 the offsets repeat every Π = 6 pairs, so pairs 3 and 9, which are both plaintext `AT` in the same class, both become `TH` after Stage I and the same ciphertext pair `HA` after Stage II.

# 5. Reference implementation

**Source repository:** https://github.com/HamzaSaleem56/NIS_CCP (public).

The solution is implemented in Python 3 with no third-party runtime dependency for encryption, decryption, or cryptanalysis. Matplotlib is used only to regenerate report charts.

| File | Responsibility |
|---|---|
| `src/cipher.py` | Normalization, key validation, Vigenère, Hill, VHC, Shift baseline, CLI |
| `src/attack.py` | IC, chi-squared, quadgram model, frequency and known-prefix attacks |
| `src/experiment.py` | Seeded trials, raw CSV output, summaries, benchmarks, charts |
| `tests/test_cipher.py` | Standard vectors, inverse properties, boundary cases, attack recovery |
| `data/` | Separate training and evaluation language corpora with attribution |
| `results/` | Actual measurements, metadata, and generated figures |

Representative commands are:

```bash
python3 src/cipher.py encrypt --key CRYPTOGRAPHY --hill-key HILL \
    --text "MEET AT THE LIBRARY AT SIX PM"
python3 src/cipher.py decrypt --key CRYPTOGRAPHY --hill-key HILL \
    --text GVAGHADTCSTYJGBWHAETLLT
python3 src/cipher.py matrix --hill-key HILL
python3 src/attack.py frequency --cipher-file ciphertext.txt
python3 src/attack.py known --known-file known_prefix.txt --cipher-file ciphertext.txt
python3 -m unittest discover -s tests -v
python3 src/experiment.py --trials 20 --seed 20261108
```

# 6. Attack methodology

## 6.1 Attacker knowledge and success criterion

Two attacker models are evaluated separately. The **ciphertext-only** attacker has C, the public algorithm, the fact that L ≥ 10, a maximum key length of 20, and general English statistics. The **known-prefix** attacker additionally has the first m normalized plaintext characters. Neither attacker receives K or H.

An attempt counts as successful only when the entire recovered normalized plaintext exactly equals the original. Partial or readable guesses are not counted as exact successes. Mean letter accuracy is reported separately to expose near-misses.

A naive brute-force search would have to try 157,248 Hill matrices for every one of 26ᴸ Vigenère keys. Both attacks avoid this by using the structure from Section 2.4.

## 6.2 Frequency-only attack

Decryption of pair j can be written one letter at a time. If (a, b) is a row of H⁻¹, then:

> plaintext letter = (a · c₁ + b · c₂ − s) mod 26

where s is the key shift for that row and that offset class. So **each row of H⁻¹ can be found on its own**: only 26² row choices exist, compared with 157,248 full matrices.

### Step A: enumerate the offset period

For each candidate key length L = 10…20, the offset period is Π = L / gcd(L, 2). Each pair belongs to class j mod Π, and all pairs in one class share the same shift.

### Step B: rank Hill rows with the index of coincidence

For every candidate row (a, b), compute uⱼ = a·c₁ + b·c₂ mod 26 for every pair, split the values into Π classes, and average the IC of the classes [2]:

> IC = [Σ fₐ(fₐ − 1)] / [n(n − 1)]

For a true row of H⁻¹, every class is English shifted by a constant, so the IC is close to English (≈ 0.066). For a wrong row, letters are mixed and the IC falls toward the uniform value (≈ 0.038). Two facts shrink the search further. A valid row cannot have both entries even or both divisible by 13, which leaves 504 rows. Multiplying a row by any of the 12 numbers that are invertible mod 26 only relabels the letters, which leaves the IC unchanged, so the 504 rows fall into 42 groups that are ranked once each. Key lengths are ranked by the IC of their two best rows; the best four lengths and the best six row groups for each are kept.

### Step C: recover multiples and shifts with chi-squared

For each kept row group, all 12 multiples and all 26 shifts per class are tested. Observed letter counts Oₐ are compared with expected English counts Eₐ:

> χ² = Σ (Oₐ − Eₐ)² / Eₐ

The shift with minimum χ² in each class gives that class's key shift, and the two multiples with the lowest total χ² are kept. This is ordinary frequency analysis applied independently to each offset class [2].

### Step D: assemble matrices and rerank with quadgrams

Pairs of different kept rows form candidate inverse matrices. Matrices that are not invertible are skipped. Each remaining candidate decrypts the whole ciphertext, and a character-quadgram model scores it in reading order. The model is trained on 600,000 letters from *Pride and Prejudice* and *The Adventures of Sherlock Holmes*. Add-k smoothing assigns a finite penalty to unseen quadgrams. Evaluation uses a different work, *A Tale of Two Cities*, reducing training/test leakage [6]–[8]. The highest-scoring candidate gives the plaintext, the Hill key (by inverting the recovered H⁻¹) and the Vigenère key (from the recovered shifts).

![Figure 2. Frequency-only attack pipeline.](../results/attack_pipeline.png)

With the configured bounds, one attempt evaluated between about 200 and 260 complete candidates on average, compared with the 157,248 × 26ᴸ keys of a brute-force search.

## 6.3 Partial-known-plaintext attack

Let the attacker know P₀…Pₘ₋₁ and the complete C. From Section 2.4, two known pairs i and j in the same offset class share the same offset w, so subtracting them removes it:

> Cᵢ − Cⱼ = H · (Pᵢ − Pⱼ) mod 26

This is the classic known-plaintext attack on the Hill cipher [1], [3], applied to differences. For each candidate key length L = 10…20:

1. Group the known pairs by class j mod Π and form all same-class differences (ΔP, ΔC).
2. Find two differences whose plaintext columns form an invertible matrix D, and solve H = E · D⁻¹ mod 26, where E holds the matching ciphertext differences.
3. Check H against every other difference. Reject L if any check fails.
4. Recover each class's Vigenère shifts as kⱼ = H⁻¹ · Cⱼ − Pⱼ and reject L if a class gives two different answers.
5. Decrypt the complete ciphertext, confirm that it reproduces the known prefix, and score it with the quadgram model.

The attack needs at least one known pair in every class plus two independent same-class differences, so the prefix must be roughly m ≥ 2Π + 4 letters. That is about L + 4 letters for an even-length key and about 2L + 4 for an odd-length key. The key recovery itself is algebraic rather than a search over 157,248 matrices or 26ᴸ keywords.

# 7. Experimental method

The experiment is deterministic under seed `20261108` and uses 20 trials per configuration. Trial messages are sampled from the separate evaluation corpus. Ten key pairs are rotated: Vigenère keywords of 10, 11 and 12 letters, each paired with a different valid 4-letter Hill key (`HILL`, `JUMP`, `RUSH`, `LAMB`, `BOLT`, `FERN`, `REEF`, `VOLT`, `HYMN`, `JOLT`). Frequency attacks are run at six ciphertext lengths: 100, 200, 400, 800, 1,600, and 3,200 characters. The known-prefix attack is tested at the same lengths with m = 32; a second experiment varies m over 16, 24, 32, 48, and 96 for 1,600-character messages.

Runtime is measured with `time.perf_counter()` and excludes one-time corpus loading. Encryption benchmarks use 21 repetitions through 100,000 characters and seven at one million characters; medians are emphasized to reduce outlier influence. Exact-success uncertainty is summarized with 95% Wilson score intervals, which are more informative than treating 20 trials as a universal probability.

The measurement environment was Python 3.13 on Linux, x86-64, with an Intel Xeon processor at 2.10 GHz (2 logical CPUs). All code was single-threaded. Timings describe this environment only; success percentages describe this corpus, key set, and configured search bounds rather than every possible natural-language message.

# 8. Attack results and interpretation

## 8.1 Frequency-only attack

{{FREQUENCY_TABLE}}

![Figure 3. Exact attack success by ciphertext length; 20 trials per point.](../results/attack_success.png)

The trend has a clear statistical explanation. At 100 characters there are only 50 pairs; with a 12-letter key they spread over 6 classes of about 8 values each, and with an 11-letter key over 11 classes of under 5 values each. That is too little evidence for the IC to pick the right rows or for chi-squared to pick the right shifts, so no message was recovered and mean letter accuracy was only 8.6%. At 200 characters exact recovery rose to 30% (70.45% mean letter accuracy), and at 400 it reached 85%. From 800 characters onward, every trial in this experiment recovered the exact message, the Hill key and an equivalent Vigenère key.

Compared with a plain Vigenère cipher, the Hill stage makes the attack need more ciphertext, because each class now holds pairs rather than single letters and the rows must be found before the shifts. It does not stop the attack.

This is not a claim of guaranteed success above 800 characters. The 95% Wilson interval for 20/20 successes is 83.89%–100%, and atypical or very short documents, non-English text, and keys outside the tested bounds can reduce performance. The honest conclusion is narrower and more useful: **ordinary long English messages leak enough repeated-key statistics for this implementation to become highly reliable**.

## 8.2 Known-prefix attack

{{KNOWN_TABLE}}

Every 32-prefix configuration achieved exact recovery in under 3 ms. Runtime grows slowly with message length because only the final candidates are decrypted and scored. The mean candidate count of about 1.5 means that, after the algebraic checks, usually only one or two key lengths survived. Ten-letter keys also pass as twenty-letter keys, which decrypt to the same message.

{{PREFIX_TABLE}}

The prefix sweep matches the requirement from Section 6.3. With 16 known letters, most attempts lacked a pair in every class or two independent differences. With 24 letters, every even-length key (10 or 12 letters, needing about 14–16) was broken, but the 11-letter key was not: an odd key length doubles the period to Π = 11 pairs and needs about 26 letters. From 32 letters onward every key was broken.

![Figure 4. Median attack runtime on logarithmic axes.](../results/attack_runtime.png)

# 9. Security analysis

## 9.1 Where the design helps

The Vigenère stage removes the trivial 25-key search of a single Shift cipher. The Hill stage adds a second, independent secret and mixes letters in pairs, so each ciphertext letter depends on two plaintext letters and two key letters. As a result, single-letter frequencies of the ciphertext no longer look like a shifted English alphabet, and a standard Vigenère attack applied directly to the ciphertext fails. A naive search over a 12-letter keyword and a Hill matrix would face 26¹² × 157,248 ≈ 1.5 × 10²² key combinations.

These properties are meaningful educationally: the cascade combines a polyalphabetic substitution with a polygraphic one and shows why a product cipher must be analyzed as a complete system rather than one stage at a time.

## 9.2 Why the design still fails

**The stages collapse into one structure.** Section 2.4 shows that Hill(Vigenère(P)) equals H·P plus a repeating offset. Because the Hill stage is linear, it does not hide the period of the Vigenère key; it only moves it from letters to pairs.

**Rows of the Hill inverse can be found one at a time.** Each plaintext letter depends on one row of H⁻¹, so the attacker searches 42 row groups instead of 157,248 matrices, and the Vigenère shifts are then found class by class with frequency analysis. The nominal key space of 10²² is never searched.

**Identical blocks leak.** The same plaintext pair in the same class always gives the same ciphertext pair, as the repeated `AT` → `HA` pair in the worked example shows.

**Known plaintext is catastrophic.** Subtracting same-class pairs cancels the Vigenère offsets completely and leaves the textbook Hill known-plaintext problem. About L + 4 known letters (2L + 4 for odd L) reveal both keys and the whole message.

**No modern security properties.** There is no random nonce, no nonlinear S-box, no authenticated integrity, and no protection against active modification. Classical letter statistics remain visible to software.

The measured results therefore support a central cryptologic lesson: **combining two weak operations does not automatically produce a strong operation**. Here two linear stages combine into one linear structure. Security must be evaluated against concrete attacks, not visual ciphertext randomness or nominal key length alone.

# 10. Complexity and efficiency

## 10.1 Asymptotic analysis

Let n be message length, M = 11 the number of candidate key lengths (10…20), G = 42 the number of Hill row groups, Q = 4 the shortlisted key lengths, S = 6 the shortlisted row groups, E the number of complete candidates scored, and m the known prefix length.

| Operation | Time | Auxiliary space | Reason |
|---|---|---|---|
| Vigenère encrypt/decrypt | O(n) | O(n) | One modular addition per character |
| Hill encrypt/decrypt | O(n) | O(n) | Four multiplications and two additions per pair; inverse matrix is O(1) |
| VHC encrypt/decrypt | O(n) | O(n) | Two sequential linear stages |
| Shift encrypt/decrypt | O(n) | O(n) | One linear substitution pass |
| Frequency attack | O(G·M·n + Q·S·12·Π·26² + E·n) | O(G·n + corpus model) | Row projection and IC ranking; chi-squared on class histograms; quadgram scoring of E candidates |
| Known-prefix attack | O(M·m² + M·n) | O(m + n) | Same-class differences and matrix solve per length; one full decryption per surviving length |

For fixed bounds the frequency attack is linear in n with a large constant: the chi-squared stage works on histograms, so its cost does not grow with message length. The known-prefix attack is also linear in n and needs only a handful of full decryptions.

## 10.2 Measured encryption and decryption performance

{{PERFORMANCE_TABLE}}

![Figure 5. Median runtime of Shift, Vigenère, Hill, and VHC operations.](../results/performance.png)

{{PERFORMANCE_ANALYSIS}} This is consistent with the two-stage design: the asymptotic class remains O(n), but the constant work and memory traffic roughly double, because every character passes through two stages instead of one. On its own, the Hill stage costs about the same as a Shift pass. Smaller inputs show more interpreter and setup overhead, so ratios should not be treated as fixed hardware-independent constants. Some adjacent measurements are non-monotonic because of normal scheduling and cache noise; using medians reduces, but does not eliminate, that variability.

The frequency attack is much more expensive than encryption because it ranks hundreds of row and length combinations and scores about 200–260 complete candidates. Known-plaintext recovery is far cheaper because the algebra eliminates almost every wrong key length before any full decryption.

# 11. Improvements without major complexity growth

| Improvement | Security effect | Cost and residual limitation |
|---|---|---|
| Require an odd Vigenère key length | Doubles the offset period Π (L instead of L/2), halving the samples per class and roughly doubling the known prefix needed | No extra computation; long ciphertexts still leak |
| Use a 3×3 Hill matrix | Mixes three letters per block, raises row candidates from 26² to 26³ and needs more ciphertext per class | About 1.5× the multiplications; still linear and still broken by known plaintext |
| Chain the Hill blocks (add the previous ciphertext pair before multiplying, like CBC mode) | Identical plaintext pairs no longer give identical ciphertext pairs and the offset no longer repeats cleanly | Same O(n) cost; an error spreads to the next pair; still linear |
| Use an autokey/running-key Vigenère instead of a repeating keyword | Removes the fixed period, so the class grouping used by both attacks breaks down | More state and careful synchronization; plaintext feedback can introduce other weaknesses |
| Add a keyed columnar transposition stage | Breaks the alignment between pairs and key positions, so the attacker must also find a permutation | One extra linear pass; vulnerable to anagramming and known structure |

These changes can raise attack effort for a classroom exercise, but none should be represented as production-grade security. For real confidentiality and integrity, the correct engineering decision is to replace the construction with a reviewed authenticated-encryption scheme such as AES-GCM or ChaCha20-Poly1305, using a maintained library, unique nonces, and proper key management.

# 12. Limitations and validity threats

- Twenty trials per configuration provide useful comparative evidence but not exact population probabilities; Wilson intervals are included for that reason.
- Minimum key length is not minimum key entropy. Repetitive keywords such as `AAAAAAAAAA` or `ABABABABAB` pass length validation but have a much shorter effective period; strong keywords should be long and non-repetitive.
- The frequency attack can return an equivalent keyword instead of the original text, for example `NETWORKSECNETWORKSEC` for `NETWORKSEC`; both decrypt identically. Exact plaintext recovery is therefore the primary success criterion, and exact key recovery is recorded separately in the raw CSV files.
- The language model and plaintexts are English. Other languages, compressed data, random strings, or highly technical text can change frequency-attack success.
- The tested keywords contain 10–12 letters and the attacker searches lengths through 20. Longer or odd-length keywords need more ciphertext per class and a longer known prefix.
- The frequency attack keeps only four key lengths and six row groups per length. This bounds cost but can exclude the true rows on short or noisy ciphertext, so the shortlist is a recall limitation rather than a proof that other candidates are impossible.
- The odd final letter is protected by the Vigenère stage only. This affects at most one letter per message and is recovered by both attacks.
- Exact recovery is strict and may understate partial cryptanalytic progress; mean letter accuracy is therefore included.
- Runtime measurements are single-machine and single-threaded. They should be compared within this experiment, not treated as universal benchmarks.

# 13. Conclusion

VHC satisfies the assignment's two-stage classical-design requirement with two ciphers from the course, a reversible Vigenère substitution followed by a 2×2 Hill cipher, together with a validated keyword of at least 10 characters, arbitrary-length A–Z handling, and a complete Python implementation. The project also demonstrates that correct encryption is only half of cipher design: explicit attacks expose whether the construction meaningfully resists analysis.

The analysis showed that the two linear stages combine into a Hill cipher with a repeating offset. The frequency attack used that structure to recover every message of 800 characters or more, and a 32-letter known prefix was enough to recover every message in the tested configurations within milliseconds. Both encryption and decryption remain O(n), at roughly twice the measured large-message cost of a Shift baseline. The strongest conclusion is therefore not that the cascade is secure, but that its exact weakness can be explained, implemented, measured, and reproduced.

# References

[1] W. Stallings, *Cryptography and Network Security: Principles and Practice*, 8th ed. Pearson, 2020. Classical substitution ciphers, the Hill cipher, and cryptanalysis foundations.

[2] D. Mukhopadhyay, “Cryptanalysis,” IIT Kharagpur cryptography course slides. Vigenère cryptanalysis, Kasiski examination, and index of coincidence. https://cse.iitkgp.ac.in/~debdeep/courses_iitkgp/Crypto/slides/cryptanalysis.pdf (accessed 2 November 2026).

[3] L. S. Hill, “Cryptography in an Algebraic Alphabet,” *The American Mathematical Monthly*, vol. 36, no. 6, pp. 306–312, 1929. Original description of the matrix cipher.

[4] EPFL Graph Search, “Auguste Kerckhoffs.” Summary of Kerckhoffs's design principles and key-secrecy principle. https://graphsearch.epfl.ch/en/concept/240985 (accessed 2 November 2026).

[5] C. Corning, “Cryptanalysis of the Vigenère's Cipher,” Georgia Southern University Research Symposium, 2014. https://digitalcommons.georgiasouthern.edu/gurc/2014/2014/78/ (accessed 2 November 2026).

[6] J. Austen, *Pride and Prejudice*. Project Gutenberg eBook 1342. https://www.gutenberg.org/ebooks/1342 (training corpus; accessed 2 November 2026).

[7] A. C. Doyle, *The Adventures of Sherlock Holmes*. Project Gutenberg eBook 1661. https://www.gutenberg.org/ebooks/1661 (training corpus; accessed 2 November 2026).

[8] C. Dickens, *A Tale of Two Cities*. Project Gutenberg eBook 98. https://www.gutenberg.org/ebooks/98 (separate evaluation corpus; accessed 2 November 2026).
