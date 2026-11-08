from __future__ import annotations
import argparse
import json
import math
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from cipher import MAX_RAILS, MIN_KEY_LENGTH, normalize, rail_fence_decrypt, vigenere_decrypt
ENGLISH_FREQUENCIES = (0.082, 0.015, 0.028, 0.043, 0.127, 0.022, 0.02, 0.061, 0.07, 0.0015, 0.0077, 0.04, 0.024, 0.067, 0.075, 0.019, 0.00095, 0.06, 0.063, 0.091, 0.028, 0.0098, 0.024, 0.0015, 0.02, 0.00074)
ENGLISH_IC = 0.066
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

    def score(self, text: str) -> float:
        normalized = normalize(text)
        if len(normalized) < 4:
            return -100.0
        total = 0.0
        for i in range(len(normalized) - 3):
            gram = normalized[i:i + 4]
            probability = (self.counts.get(gram, 0) + 0.1) / self.denominator
            total += math.log10(probability) if gram in self.counts else self.unknown
        return total / (len(normalized) - 3)

@dataclass
class AttackResult:
    candidate_found: bool
    plaintext: str = ''
    key: str = ''
    rails: int = 0
    key_length: int = 0
    score: float = -100.0
    evaluated_candidates: int = 0
    elapsed_ms: float = 0.0

def index_of_coincidence(text: str) -> float:
    counts = Counter(text)
    n = len(text)
    if n < 2:
        return 0.0
    return sum((count * (count - 1) for count in counts.values())) / (n * (n - 1))

def average_column_ic(ciphertext: str, key_length: int) -> float:
    columns = [ciphertext[i::key_length] for i in range(key_length)]
    nonempty = [column for column in columns if len(column) > 1]
    if not nonempty:
        return 0.0
    return sum((index_of_coincidence(column) for column in nonempty)) / len(nonempty)

def _chi_squared_shift(column: str, shift: int) -> float:
    n = len(column)
    if not n:
        return math.inf
    decrypted = [chr((ord(ch) - 65 - shift) % 26 + 65) for ch in column]
    counts = Counter(decrypted)
    return sum(((counts.get(chr(65 + i), 0) - n * ENGLISH_FREQUENCIES[i]) ** 2 / (n * ENGLISH_FREQUENCIES[i]) for i in range(26)))

def recover_vigenere_key(ciphertext: str, key_length: int) -> str:
    shifts = []
    for i in range(key_length):
        column = ciphertext[i::key_length]
        shift = min(range(26), key=lambda candidate: _chi_squared_shift(column, candidate))
        shifts.append(shift)
    return ''.join((chr(65 + shift) for shift in shifts))

def frequency_attack(ciphertext: str, model: QuadgramModel, max_rails: int=MAX_RAILS, max_key_length: int=20, ic_shortlist: int=8) -> AttackResult:
    started = time.perf_counter()
    normalized = normalize(ciphertext)
    best = AttackResult(candidate_found=False)
    if len(normalized) < 4:
        best.elapsed_ms = (time.perf_counter() - started) * 1000
        return best
    evaluations = 0
    for rails in range(2, max_rails + 1):
        stage_one = rail_fence_decrypt(normalized, rails)
        upper = min(max_key_length, len(stage_one))
        lengths = list(range(1, upper + 1))
        lengths.sort(key=lambda length: abs(average_column_ic(stage_one, length) - ENGLISH_IC))
        for key_length in lengths[:max(1, min(ic_shortlist, len(lengths)))]:
            key = recover_vigenere_key(stage_one, key_length)
            candidate = vigenere_decrypt(stage_one, key)
            score = model.score(candidate)
            evaluations += 1
            if score > best.score:
                best = AttackResult(candidate_found=True, plaintext=candidate, key=key, rails=rails, key_length=key_length, score=score, evaluated_candidates=evaluations)
    best.evaluated_candidates = evaluations
    best.elapsed_ms = (time.perf_counter() - started) * 1000
    return best

def known_plaintext_attack(known_prefix: str, ciphertext: str, model: QuadgramModel, max_rails: int=MAX_RAILS, max_key_length: int=20) -> AttackResult:
    started = time.perf_counter()
    known = normalize(known_prefix)
    normalized = normalize(ciphertext)
    best = AttackResult(candidate_found=False)
    if not known or len(known) > len(normalized) or len(known) < MIN_KEY_LENGTH:
        best.elapsed_ms = (time.perf_counter() - started) * 1000
        return best
    evaluations = 0
    for rails in range(2, max_rails + 1):
        stage_one = rail_fence_decrypt(normalized, rails)
        key_stream = [(ord(stage_one[i]) - ord(known[i])) % 26 for i in range(len(known))]
        for key_length in range(MIN_KEY_LENGTH, min(max_key_length, len(known)) + 1):
            if any((key_stream[i] != key_stream[i % key_length] for i in range(len(known)))):
                continue
            key = ''.join((chr(65 + value) for value in key_stream[:key_length]))
            candidate = vigenere_decrypt(stage_one, key)
            evaluations += 1
            score = model.score(candidate)
            if score > best.score:
                best = AttackResult(candidate_found=True, plaintext=candidate, key=key, rails=rails, key_length=key_length, score=score, evaluated_candidates=evaluations)
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
