from __future__ import annotations
import argparse
from pathlib import Path
from typing import Iterator
ALPHABET_SIZE = 26
MIN_KEY_LENGTH = 10
MIN_RAILS = 2
MAX_RAILS = 8

def normalize(text: str) -> str:
    return ''.join((ch.upper() for ch in text if ch.isascii() and ch.isalpha()))

def validate_key(key: str, minimum: int=MIN_KEY_LENGTH) -> str:
    normalized = normalize(key)
    if len(normalized) < minimum:
        raise ValueError(f'Key must contain at least {minimum} A-Z letters')
    return normalized

def derive_rails(key: str) -> int:
    normalized = validate_key(key)
    weighted_sum = sum(((i + 1) * (ord(ch) - 64) for i, ch in enumerate(normalized)))
    return MIN_RAILS + weighted_sum % (MAX_RAILS - MIN_RAILS + 1)

def validate_rails(rails: int) -> int:
    if not MIN_RAILS <= rails <= MAX_RAILS:
        raise ValueError(f'Rail count must be between {MIN_RAILS} and {MAX_RAILS}')
    return rails

def _shift_char(ch: str, amount: int) -> str:
    return chr((ord(ch) - 65 + amount) % ALPHABET_SIZE + 65)

def vigenere_encrypt(plaintext: str, key: str) -> str:
    text = normalize(plaintext)
    normalized_key = validate_key(key, minimum=1)
    shifts = [ord(ch) - 65 for ch in normalized_key]
    return ''.join((_shift_char(ch, shifts[i % len(shifts)]) for i, ch in enumerate(text)))

def vigenere_decrypt(ciphertext: str, key: str) -> str:
    text = normalize(ciphertext)
    normalized_key = validate_key(key, minimum=1)
    shifts = [ord(ch) - 65 for ch in normalized_key]
    return ''.join((_shift_char(ch, -shifts[i % len(shifts)]) for i, ch in enumerate(text)))

def _rail_indices(length: int, rails: int) -> Iterator[int]:
    if rails < MIN_RAILS:
        raise ValueError(f'Rail count must be at least {MIN_RAILS}')
    period = 2 * rails - 2
    for i in range(length):
        position = i % period
        yield (position if position < rails else period - position)

def rail_fence_encrypt(plaintext: str, rails: int) -> str:
    text = normalize(plaintext)
    rows: list[list[str]] = [[] for _ in range(rails)]
    for ch, row in zip(text, _rail_indices(len(text), rails)):
        rows[row].append(ch)
    return ''.join((''.join(row) for row in rows))

def rail_fence_decrypt(ciphertext: str, rails: int) -> str:
    text = normalize(ciphertext)
    indices = list(_rail_indices(len(text), rails))
    counts = [0] * rails
    for row in indices:
        counts[row] += 1
    rows: list[str] = []
    offset = 0
    for count in counts:
        rows.append(text[offset:offset + count])
        offset += count
    offsets = [0] * rails
    output: list[str] = []
    for row in indices:
        output.append(rows[row][offsets[row]])
        offsets[row] += 1
    return ''.join(output)

def encrypt(plaintext: str, key: str, rails: int | None=None) -> str:
    normalized_key = validate_key(key)
    rail_count = derive_rails(normalized_key) if rails is None else validate_rails(rails)
    stage_one = vigenere_encrypt(plaintext, normalized_key)
    return rail_fence_encrypt(stage_one, rail_count)

def decrypt(ciphertext: str, key: str, rails: int | None=None) -> str:
    normalized_key = validate_key(key)
    rail_count = derive_rails(normalized_key) if rails is None else validate_rails(rails)
    stage_one = rail_fence_decrypt(ciphertext, rail_count)
    return vigenere_decrypt(stage_one, normalized_key)

def shift_encrypt(plaintext: str, shift: int=3) -> str:
    return ''.join((_shift_char(ch, shift) for ch in normalize(plaintext)))

def shift_decrypt(ciphertext: str, shift: int=3) -> str:
    return shift_encrypt(ciphertext, -shift)

def _read_text(text: str | None, input_path: str | None) -> str:
    if text is not None:
        return text
    if input_path:
        return Path(input_path).read_text(encoding='utf-8')
    raise ValueError('Provide --text or --input')

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('encrypt', 'decrypt', 'rails'))
    parser.add_argument('--key', required=True, help='At least 10 A-Z letters')
    parser.add_argument('--text', help='Input text; omit when using --input')
    parser.add_argument('--input', help='UTF-8 input file')
    parser.add_argument('--rails', type=int, help='Override key-derived rail count')
    args = parser.parse_args()
    try:
        if args.command == 'rails':
            print(derive_rails(args.key))
            return
        result = encrypt(_read_text(args.text, args.input), args.key, args.rails) if args.command == 'encrypt' else decrypt(_read_text(args.text, args.input), args.key, args.rails)
        print(result)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
if __name__ == '__main__':
    main()
