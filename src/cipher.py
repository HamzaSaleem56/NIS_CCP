from __future__ import annotations
import argparse
from math import gcd
from pathlib import Path
ALPHABET_SIZE = 26
MIN_KEY_LENGTH = 10
HILL_KEY_LENGTH = 4
Matrix = tuple[tuple[int, int], tuple[int, int]]

def normalize(text: str) -> str:
    return ''.join((ch.upper() for ch in text if ch.isascii() and ch.isalpha()))

def validate_key(key: str, minimum: int=MIN_KEY_LENGTH) -> str:
    normalized = normalize(key)
    if len(normalized) < minimum:
        raise ValueError(f'Key must contain at least {minimum} A-Z letters')
    return normalized

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

def determinant(matrix: Matrix) -> int:
    return (matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) % ALPHABET_SIZE

def is_invertible(matrix: Matrix) -> bool:
    return gcd(determinant(matrix), ALPHABET_SIZE) == 1

def matrix_inverse(matrix: Matrix) -> Matrix:
    det = determinant(matrix)
    if gcd(det, ALPHABET_SIZE) != 1:
        raise ValueError('Hill key matrix is not invertible mod 26 (determinant must share no factor with 26)')
    det_inv = pow(det, -1, ALPHABET_SIZE)
    (a, b), (c, d) = matrix
    return ((d * det_inv % 26, -b * det_inv % 26), (-c * det_inv % 26, a * det_inv % 26))

def hill_matrix(hill_key: str) -> Matrix:
    normalized = normalize(hill_key)
    if len(normalized) != HILL_KEY_LENGTH:
        raise ValueError(f'Hill key must contain exactly {HILL_KEY_LENGTH} A-Z letters')
    values = [ord(ch) - 65 for ch in normalized]
    matrix = ((values[0], values[1]), (values[2], values[3]))
    if not is_invertible(matrix):
        raise ValueError(f'Hill key {normalized} gives determinant {determinant(matrix)}, which is not invertible mod 26; choose a key whose determinant is odd and not 13')
    return matrix

def _apply_matrix(text: str, matrix: Matrix) -> str:
    (a, b), (c, d) = matrix
    output: list[str] = []
    paired_length = len(text) - len(text) % 2
    for i in range(0, paired_length, 2):
        x = ord(text[i]) - 65
        y = ord(text[i + 1]) - 65
        output.append(chr((a * x + b * y) % 26 + 65))
        output.append(chr((c * x + d * y) % 26 + 65))
    output.append(text[paired_length:])
    return ''.join(output)

def hill_encrypt(plaintext: str, hill_key: str) -> str:
    return _apply_matrix(normalize(plaintext), hill_matrix(hill_key))

def hill_decrypt(ciphertext: str, hill_key: str) -> str:
    return _apply_matrix(normalize(ciphertext), matrix_inverse(hill_matrix(hill_key)))

def encrypt(plaintext: str, key: str, hill_key: str) -> str:
    stage_one = vigenere_encrypt(plaintext, validate_key(key))
    return hill_encrypt(stage_one, hill_key)

def decrypt(ciphertext: str, key: str, hill_key: str) -> str:
    stage_one = hill_decrypt(ciphertext, hill_key)
    return vigenere_decrypt(stage_one, validate_key(key))

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
    parser.add_argument('command', choices=('encrypt', 'decrypt', 'matrix'))
    parser.add_argument('--key', help='Vigenère key: at least 10 A-Z letters')
    parser.add_argument('--hill-key', required=True, help='Hill key: exactly 4 A-Z letters forming an invertible 2x2 matrix')
    parser.add_argument('--text', help='Input text; omit when using --input')
    parser.add_argument('--input', help='UTF-8 input file')
    args = parser.parse_args()
    try:
        if args.command == 'matrix':
            matrix = hill_matrix(args.hill_key)
            print(f'H = {matrix}, det = {determinant(matrix)}, H^-1 = {matrix_inverse(matrix)}')
            return
        if not args.key:
            raise ValueError('--key is required for encrypt and decrypt')
        text = _read_text(args.text, args.input)
        result = encrypt(text, args.key, args.hill_key) if args.command == 'encrypt' else decrypt(text, args.key, args.hill_key)
        print(result)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
if __name__ == '__main__':
    main()
