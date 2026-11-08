**VERDICT: PASS** — math is correct (Vigenère, rail fence, and their composition round-trip: `decrypt(encrypt(m, k), k) == normalize(m)`; rail range formula `2 + s % 7` correctly yields 2–8; rail fence decrypt correctly reconstructs zigzag via per-row counts).

**Minor issues (non-fatal):**

1. **`--rails` override not range-validated.** Values ≥ 9 are accepted, violating the 2–8 design bounds; values < 2 raise only via `_rail_indices`, i.e., **only when text is non-empty** — an empty input with `--rails 1` silently succeeds instead of erroring. Validate `2 <= rails <= 8` up front in `encrypt`/`decrypt` or the CLI.

2. **Key-length policy inconsistency.** `encrypt`/`decrypt` enforce ≥10 letters, but `vigenere_encrypt`/`vigenere_decrypt` accept 1. Intentional layering is fine, but the standalone functions can produce ciphertext the CLI path would then reject keys for — document or align.

3. **Silent data loss by design (confirm against assignment).** `normalize` drops all non-A-Z characters (spaces, digits, Unicode), so plaintext ≠ decrypted output for general input. Standard for classical ciphers, but verify the assignment doesn't require preserving non-letters (e.g., passing them through).

4. **Dead code:** `shift_encrypt`/`shift_decrypt` (Caesar) are unused by the composed cipher and CLI. Harmless, but remove if the assignment is strictly Vigenère+rail fence.

**Checked and clean:** negative-shift Vigenère inverse; key index wraparound `i % len`; rail period `2r−2` and mirror `period − position`; decrypt row-slicing matches encrypt row-concatenation order; `UnicodeDecodeError` is a `ValueError` subclass, so the CLI's exception handler covers bad file encoding; empty-string edge cases behave.
