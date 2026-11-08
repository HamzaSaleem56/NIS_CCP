from __future__ import annotations
import argparse
import json
import math
import time
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import combinations
from math import gcd
from pathlib import Path
from cipher import MIN_KEY_LENGTH, Matrix, determinant, is_invertible, matrix_inverse, normalize
ENGLISH_FREQUENCIES = (0.082, 0.015, 0.028, 0.043, 0.127, 0.022, 0.02, 0.061, 0.07, 0.0015, 0.0077, 0.04, 0.024, 0.067, 0.075, 0.019, 0.00095, 0.06, 0.063, 0.091, 0.028, 0.0098, 0.024, 0.0015, 0.02, 0.00074)
ENGLISH_IC = 0.066
UNITS = tuple((k for k in range(1, 26) if gcd(k, 26) == 1))
DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / 'data' / 'english_corpus.txt'

class QuadgramModel:

    def __init__(self, corpus_path: str | Path=DEFAULT_CORPUS):
        text = normalize(Path(corpus_path).read_text(encoding='utf-8'))
        if len(text) < 4:
            raise ValueError('Quadgram training corpus is too short')
        self.counts = Counter((text[i:i + 4] for i in range(len(text) - 3)))
        self.total = sum(self.counts.values())
        self.denominator = self.total + 0.1 * 26 ** 4
        self.unknown = math.log10(0.1 / self.denominator)
        self.table = {gram: math.log10((count + 0.1) / self.denominator) for gram, count in self.counts.items()}

    def score(self, text: str) -> float:
        normalized = normalize(text)
        if len(normalized) < 4:
            return -100.0
        table = self.table
        unknown = self.unknown
        total = sum((table.get(normalized[i:i + 4], unknown) for i in range(len(normalized) - 3)))
        return total / (len(normalized) - 3)

@dataclass
class AttackResult:
    candidate_found: bool
    plaintext: str = ''
    key: str = ''
    hill_key: str = ''
    key_length: int = 0
    score: float = -100.0
    evaluated_candidates: int = 0
    elapsed_ms: float = 0.0

def index_of_coincidence(values) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    return sum((count * (count - 1) for count in Counter(values).values())) / (n * (n - 1))

def _canonical_row(a: int, b: int) -> tuple[int, int]:
    return min(((k * a % 26, k * b % 26) for k in UNITS))

def candidate_rows() -> list[tuple[int, int]]:
    return sorted({_canonical_row(a, b) for a in range(26) for b in range(26) if gcd(gcd(a, b), 26) == 1})
ROW_CLASSES = candidate_rows()

def block_period(key_length: int) -> int:
    return key_length // gcd(key_length, 2)

def _histogram(values) -> list[int]:
    counts = [0] * 26
    for value in values:
        counts[value] += 1
    return counts

def _best_shift(histogram: list[int]) -> tuple[int, float]:
    n = sum(histogram)
    if not n:
        return (0, 0.0)
    best = (0, math.inf)
    for shift in range(26):
        chi = sum((histogram[(i + shift) % 26] ** 2 / ENGLISH_FREQUENCIES[i] for i in range(26))) / n - n
        if chi < best[1]:
            best = (shift, chi)
    return best

def _scaled(histogram: list[int], unit: int) -> list[int]:
    scaled = [0] * 26
    for value, count in enumerate(histogram):
        scaled[value * unit % 26] += count
    return scaled

def _key_from_shifts(first: list[int], second: list[int], key_length: int) -> str:
    key = [0] * key_length
    for r in range(len(first)):
        key[2 * r % key_length] = first[r]
        key[(2 * r + 1) % key_length] = second[r]
    return ''.join((chr(65 + value) for value in key))

def _decrypt_with(codes: list[int], inverse: Matrix, first: list[int], second: list[int]) -> str:
    (a, b), (c, d) = inverse
    period = len(first)
    output: list[str] = []
    paired = len(codes) - len(codes) % 2
    for i in range(0, paired, 2):
        r = i // 2 % period
        x, y = (codes[i], codes[i + 1])
        output.append(chr((a * x + b * y - first[r]) % 26 + 65))
        output.append(chr((c * x + d * y - second[r]) % 26 + 65))
    if paired < len(codes):
        output.append(chr((codes[-1] - first[paired // 2 % period]) % 26 + 65))
    return ''.join(output)

def _hill_key_from_inverse(inverse: Matrix) -> str:
    matrix = matrix_inverse(inverse)
    return ''.join((chr(65 + value) for row in matrix for value in row))

def frequency_attack(ciphertext: str, model: QuadgramModel, max_key_length: int=20, period_shortlist: int=4, row_shortlist: int=6, multiples_kept: int=2) -> AttackResult:
    started = time.perf_counter()
    codes = [ord(ch) - 65 for ch in normalize(ciphertext)]
    best = AttackResult(candidate_found=False)
    if len(codes) < 4:
        best.elapsed_ms = (time.perf_counter() - started) * 1000
        return best
    xs = codes[0:len(codes) - len(codes) % 2:2]
    ys = codes[1:len(codes) - len(codes) % 2:2]
    projections = {row: [(row[0] * x + row[1] * y) % 26 for x, y in zip(xs, ys)] for row in ROW_CLASSES}
    period_rankings = []
    for key_length in range(MIN_KEY_LENGTH, max_key_length + 1):
        period = block_period(key_length)
        if period > len(xs):
            continue
        ranked_rows = []
        for row, values in projections.items():
            classes = [values[r::period] for r in range(period)]
            usable = [column for column in classes if len(column) > 1]
            ic = sum((index_of_coincidence(column) for column in usable)) / len(usable) if usable else 0.0
            ranked_rows.append((-ic, row))
        ranked_rows.sort()
        period_rankings.append((ranked_rows[0][0] + ranked_rows[1][0], key_length, period, [row for _, row in ranked_rows[:row_shortlist]]))
    period_rankings.sort()
    evaluations = 0
    for _, key_length, period, rows in period_rankings[:period_shortlist]:
        options: dict[tuple[int, int], list[tuple[float, tuple[int, int], list[int]]]] = {}
        for row in rows:
            histograms = [_histogram(projections[row][r::period]) for r in range(period)]
            scored = []
            for unit in UNITS:
                shifts = []
                total = 0.0
                for histogram in histograms:
                    shift, chi = _best_shift(_scaled(histogram, unit))
                    shifts.append(shift)
                    total += chi
                scored.append((total, (unit * row[0] % 26, unit * row[1] % 26), shifts))
            scored.sort(key=lambda item: item[0])
            options[row] = scored[:multiples_kept]
        for row_one, row_two in ((p, q) for p in rows for q in rows if p != q):
            for _, first_row, first_shifts in options[row_one]:
                for _, second_row, second_shifts in options[row_two]:
                    inverse = (first_row, second_row)
                    if not is_invertible(inverse):
                        continue
                    candidate = _decrypt_with(codes, inverse, first_shifts, second_shifts)
                    score = model.score(candidate)
                    evaluations += 1
                    if score > best.score:
                        best = AttackResult(candidate_found=True, plaintext=candidate, key=_key_from_shifts(first_shifts, second_shifts, key_length), hill_key=_hill_key_from_inverse(inverse), key_length=key_length, score=score)
    best.evaluated_candidates = evaluations
    best.elapsed_ms = (time.perf_counter() - started) * 1000
    return best

def _solve_matrix(differences: list[tuple[tuple[int, int], tuple[int, int]]]) -> Matrix | None:
    pool = list(differences)
    pool += [((p1[0] + p2[0], p1[1] + p2[1]), (c1[0] + c2[0], c1[1] + c2[1])) for (p1, c1), (p2, c2) in combinations(differences[:12], 2)]
    for (p1, c1), (p2, c2) in combinations(pool, 2):
        plain_matrix = ((p1[0] % 26, p2[0] % 26), (p1[1] % 26, p2[1] % 26))
        if not is_invertible(plain_matrix):
            continue
        inverse = matrix_inverse(plain_matrix)
        cipher_matrix = ((c1[0] % 26, c2[0] % 26), (c1[1] % 26, c2[1] % 26))
        return tuple((tuple((sum((cipher_matrix[i][t] * inverse[t][j] for t in range(2))) % 26 for j in range(2))) for i in range(2)))
    return None

def known_plaintext_attack(known_prefix: str, ciphertext: str, model: QuadgramModel, max_key_length: int=20) -> AttackResult:
    started = time.perf_counter()
    known = [ord(ch) - 65 for ch in normalize(known_prefix)]
    codes = [ord(ch) - 65 for ch in normalize(ciphertext)]
    best = AttackResult(candidate_found=False)
    if len(known) > len(codes):
        best.elapsed_ms = (time.perf_counter() - started) * 1000
        return best
    known_blocks = len(known) // 2
    plain_blocks = [(known[2 * j], known[2 * j + 1]) for j in range(known_blocks)]
    cipher_blocks = [(codes[2 * j], codes[2 * j + 1]) for j in range(known_blocks)]
    evaluations = 0
    for key_length in range(MIN_KEY_LENGTH, max_key_length + 1):
        period = block_period(key_length)
        if known_blocks < period:
            continue
        differences = []
        for r in range(period):
            members = list(range(r, known_blocks, period))
            for i, j in combinations(members, 2):
                differences.append(((plain_blocks[i][0] - plain_blocks[j][0], plain_blocks[i][1] - plain_blocks[j][1]), (cipher_blocks[i][0] - cipher_blocks[j][0], cipher_blocks[i][1] - cipher_blocks[j][1])))
        matrix = _solve_matrix(differences)
        if matrix is None or not is_invertible(matrix):
            continue
        (a, b), (c, d) = matrix
        if any(((a * p[0] + b * p[1] - q[0]) % 26 or (c * p[0] + d * p[1] - q[1]) % 26 for p, q in differences)):
            continue
        inverse = matrix_inverse(matrix)
        first: list[int] = []
        second: list[int] = []
        consistent = True
        for r in range(period):
            offsets = set()
            for j in range(r, known_blocks, period):
                x, y = cipher_blocks[j]
                offsets.add(((inverse[0][0] * x + inverse[0][1] * y - plain_blocks[j][0]) % 26, (inverse[1][0] * x + inverse[1][1] * y - plain_blocks[j][1]) % 26))
            if len(offsets) != 1:
                consistent = False
                break
            offset = offsets.pop()
            first.append(offset[0])
            second.append(offset[1])
        if not consistent:
            continue
        candidate = _decrypt_with(codes, inverse, first, second)
        evaluations += 1
        if candidate[:len(known)] != ''.join((chr(65 + v) for v in known)):
            continue
        score = model.score(candidate)
        if score > best.score:
            best = AttackResult(candidate_found=True, plaintext=candidate, key=_key_from_shifts(first, second, key_length), hill_key=_hill_key_from_inverse(inverse), key_length=key_length, score=score)
    best.evaluated_candidates = evaluations
    best.elapsed_ms = (time.perf_counter() - started) * 1000
    return best

def _load_input(value: str | None, path: str | None, label: str) -> str:
    if value is not None:
        return value
    if path:
        return Path(path).read_text(encoding='utf-8')
    raise ValueError(f'Provide {label} or its file option')

def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    for name in ('frequency', 'known'):
        sub = subparsers.add_parser(name)
        sub.add_argument('--ciphertext')
        sub.add_argument('--cipher-file')
        sub.add_argument('--corpus', default=str(DEFAULT_CORPUS))
        sub.add_argument('--max-key-length', type=int, default=20)
        if name == 'known':
            sub.add_argument('--known-prefix')
            sub.add_argument('--known-file')
    args = parser.parse_args()
    try:
        ciphertext = _load_input(args.ciphertext, args.cipher_file, '--ciphertext')
        model = QuadgramModel(args.corpus)
        if args.command == 'frequency':
            result = frequency_attack(ciphertext, model, max_key_length=args.max_key_length)
        else:
            known = _load_input(args.known_prefix, args.known_file, '--known-prefix')
            result = known_plaintext_attack(known, ciphertext, model, max_key_length=args.max_key_length)
        print(json.dumps(asdict(result), indent=2))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
if __name__ == '__main__':
    main()
