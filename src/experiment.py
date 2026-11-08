from __future__ import annotations
import argparse
import csv
import json
import random
import statistics
import time
from pathlib import Path
from attack import QuadgramModel, frequency_attack, known_plaintext_attack
from cipher import decrypt, encrypt, hill_encrypt, hill_matrix, shift_decrypt, shift_encrypt, vigenere_encrypt
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
KEYS = (('CRYPTOGRAPHY', 'HILL'), ('KERCKHOFFS', 'JUMP'), ('SUBSTITUTION', 'RUSH'), ('INFORMATION', 'LAMB'), ('CLASSICALX', 'BOLT'), ('TRANSPOSED', 'FERN'), ('FREQUENCYX', 'REEF'), ('CIPHERATTACK', 'VOLT'), ('NETWORKSEC', 'HYMN'), ('POLYALPHABET', 'JOLT'))
KNOWN_PREFIX = 32
PREFIX_LENGTHS = (16, 24, 32, 48, 96)
LENGTHS = (100, 200, 400, 800, 1600, 3200)

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def wilson_interval(successes: int, trials: int, z: float=1.96) -> tuple[float, float]:
    if not trials:
        return (0.0, 0.0)
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    margin = z * (p * (1 - p) / trials + z * z / (4 * trials * trials)) ** 0.5 / denominator
    return (100 * max(0.0, center - margin), 100 * min(1.0, center + margin))

def sample_plaintext(corpus: str, length: int, rng: random.Random) -> str:
    start = rng.randrange(0, len(corpus) - length + 1)
    return corpus[start:start + length]

def summarize_attack_rows(rows: list[dict], prefix: str) -> list[dict]:
    summary = []
    for length in LENGTHS:
        group = [row for row in rows if row['ciphertext_length'] == length]
        successes = sum((row['exact_recovery'] for row in group))
        low, high = wilson_interval(successes, len(group))
        times = [row['elapsed_ms'] for row in group]
        summary.append({'attack': prefix, 'ciphertext_length': length, 'trials': len(group), 'exact_successes': successes, 'exact_success_pct': round(100 * successes / len(group), 2), 'wilson_95_low_pct': round(low, 2), 'wilson_95_high_pct': round(high, 2), 'mean_letter_accuracy_pct': round(statistics.mean((row['letter_accuracy_pct'] for row in group)), 2), 'mean_elapsed_ms': round(statistics.mean(times), 3), 'median_elapsed_ms': round(statistics.median(times), 3), 'mean_candidates': round(statistics.mean((row['evaluated_candidates'] for row in group)), 1)})
    return summary

def run_attack_experiments(corpus: str, model: QuadgramModel, trials: int, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    frequency_rows: list[dict] = []
    known_rows: list[dict] = []
    for length in LENGTHS:
        for trial in range(trials):
            rng = random.Random(seed + length * 1000 + trial)
            plaintext = sample_plaintext(corpus, length, rng)
            key, hill_key = KEYS[trial % len(KEYS)]
            ciphertext = encrypt(plaintext, key, hill_key)
            result = frequency_attack(ciphertext, model)
            matches = sum((a == b for a, b in zip(result.plaintext, plaintext)))
            frequency_rows.append({'ciphertext_length': length, 'trial': trial, 'actual_key': key, 'actual_hill_key': hill_key, 'recovered_key': result.key, 'recovered_hill_key': result.hill_key, 'exact_recovery': int(result.plaintext == plaintext), 'key_recovery': int(result.key == key), 'hill_key_recovery': int(result.hill_key == hill_key), 'letter_accuracy_pct': round(100 * matches / length, 2), 'language_score': round(result.score, 6), 'evaluated_candidates': result.evaluated_candidates, 'elapsed_ms': round(result.elapsed_ms, 3)})
            known = known_plaintext_attack(plaintext[:KNOWN_PREFIX], ciphertext, model)
            known_matches = sum((a == b for a, b in zip(known.plaintext, plaintext)))
            known_rows.append({'ciphertext_length': length, 'known_prefix_length': KNOWN_PREFIX, 'trial': trial, 'actual_key': key, 'actual_hill_key': hill_key, 'recovered_key': known.key, 'recovered_hill_key': known.hill_key, 'exact_recovery': int(known.plaintext == plaintext), 'key_recovery': int(known.key == key), 'hill_key_recovery': int(known.hill_key == hill_key), 'letter_accuracy_pct': round(100 * known_matches / length, 2), 'language_score': round(known.score, 6), 'evaluated_candidates': known.evaluated_candidates, 'elapsed_ms': round(known.elapsed_ms, 3)})
        print(f'attacks: length={length}, trials={trials} complete', flush=True)
    summary = summarize_attack_rows(frequency_rows, 'frequency') + summarize_attack_rows(known_rows, f'known-prefix-{KNOWN_PREFIX}')
    return (frequency_rows, known_rows, summary)

def run_prefix_experiment(corpus: str, model: QuadgramModel, trials: int, seed: int) -> list[dict]:
    rows = []
    message_length = 1600
    for prefix_length in PREFIX_LENGTHS:
        for trial in range(trials):
            rng = random.Random(seed + 900000 + prefix_length * 100 + trial)
            plaintext = sample_plaintext(corpus, message_length, rng)
            key, hill_key = KEYS[trial % len(KEYS)]
            ciphertext = encrypt(plaintext, key, hill_key)
            result = known_plaintext_attack(plaintext[:prefix_length], ciphertext, model)
            rows.append({'ciphertext_length': message_length, 'known_prefix_length': prefix_length, 'trial': trial, 'key_length': len(key), 'exact_recovery': int(result.plaintext == plaintext), 'key_recovery': int(result.key == key), 'evaluated_candidates': result.evaluated_candidates, 'elapsed_ms': round(result.elapsed_ms, 3)})
    return rows

def measure(function, repeats: int) -> list[float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        function()
        samples.append((time.perf_counter() - started) * 1000)
    return samples

def run_benchmarks(corpus: str) -> list[dict]:
    rows = []
    key, hill_key = KEYS[0]
    for length in (1000, 10000, 100000, 1000000):
        plaintext = (corpus * (length // len(corpus) + 1))[:length]
        ciphertext = encrypt(plaintext, key, hill_key)
        shift_ciphertext = shift_encrypt(plaintext, 3)
        repeats = 21 if length <= 100000 else 7
        operations = {'shift_encrypt': lambda: shift_encrypt(plaintext, 3), 'shift_decrypt': lambda: shift_decrypt(shift_ciphertext, 3), 'vigenere_encrypt': lambda: vigenere_encrypt(plaintext, key), 'hill_encrypt': lambda: hill_encrypt(plaintext, hill_key), 'vhc_encrypt': lambda: encrypt(plaintext, key, hill_key), 'vhc_decrypt': lambda: decrypt(ciphertext, key, hill_key)}
        for operation, function in operations.items():
            samples = measure(function, repeats)
            median_ms = statistics.median(samples)
            rows.append({'operation': operation, 'input_length': length, 'repeats': repeats, 'median_ms': round(median_ms, 4), 'mean_ms': round(statistics.mean(samples), 4), 'min_ms': round(min(samples), 4), 'max_ms': round(max(samples), 4), 'million_chars_per_sec': round(length / (median_ms * 1000), 4)})
        print(f'benchmark: length={length} complete', flush=True)
    return rows

def make_charts(attack_summary: list[dict], benchmarks: list[dict]) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['FreeSerif', 'Liberation Serif', 'DejaVu Serif'], 'font.size': 11, 'mathtext.fontset': 'stix'})
    colors = {'frequency': '#1f3a5f', f'known-prefix-{KNOWN_PREFIX}': '#8c3b3b'}
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for attack in ('frequency', f'known-prefix-{KNOWN_PREFIX}'):
        rows = [row for row in attack_summary if row['attack'] == attack]
        ax.plot([r['ciphertext_length'] for r in rows], [r['exact_success_pct'] for r in rows], marker='o', linewidth=2.2, label=attack, color=colors[attack])
    ax.set_xscale('log', base=2)
    ax.set_xticks(LENGTHS, [str(v) for v in LENGTHS])
    ax.set_xlabel('Ciphertext length (characters)')
    ax.set_ylabel('Exact full-message recovery (%)')
    ax.set_ylim(-3, 105)
    ax.set_title('Attack success versus ciphertext length')
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / 'attack_success.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for attack in ('frequency', f'known-prefix-{KNOWN_PREFIX}'):
        rows = [row for row in attack_summary if row['attack'] == attack]
        ax.plot([r['ciphertext_length'] for r in rows], [r['median_elapsed_ms'] for r in rows], marker='o', linewidth=2.2, label=attack, color=colors[attack])
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(LENGTHS, [str(v) for v in LENGTHS])
    ax.set_xlabel('Ciphertext length (characters)')
    ax.set_ylabel('Median attack runtime (ms, log scale)')
    ax.set_title('Measured cryptanalysis effort')
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / 'attack_runtime.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for operation, color in (('shift_encrypt', '#7a7a7a'), ('vigenere_encrypt', '#4f7cac'), ('hill_encrypt', '#4d7c59'), ('vhc_encrypt', '#1f3a5f'), ('vhc_decrypt', '#8c3b3b')):
        rows = [row for row in benchmarks if row['operation'] == operation]
        ax.plot([r['input_length'] for r in rows], [r['median_ms'] for r in rows], marker='o', linewidth=2.0, label=operation, color=color)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Input length (characters)')
    ax.set_ylabel('Median runtime (ms, log scale)')
    ax.set_title('Encryption/decryption performance')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / 'performance.png', dpi=180)
    plt.close(fig)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=20)
    parser.add_argument('--seed', type=int, default=20261108)
    parser.add_argument('--charts-only', action='store_true', help='Redraw charts from the saved CSV results without rerunning')
    args = parser.parse_args()
    if args.charts_only:
        def numeric(rows):
            return [{k: (float(v) if k not in ('attack', 'operation') else v) for k, v in row.items()} for row in rows]
        with (RESULTS / 'attack_summary.csv').open(encoding='utf-8') as handle:
            summary_rows = numeric(list(csv.DictReader(handle)))
        with (RESULTS / 'performance.csv').open(encoding='utf-8') as handle:
            benchmark_rows = numeric(list(csv.DictReader(handle)))
        make_charts(summary_rows, benchmark_rows)
        print(f'Charts redrawn in {RESULTS}')
        return
    if args.trials < 1:
        parser.error('--trials must be positive')
    RESULTS.mkdir(exist_ok=True)
    corpus = (ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8')
    model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
    frequency, known, summary = run_attack_experiments(corpus, model, args.trials, args.seed)
    prefixes = run_prefix_experiment(corpus, model, args.trials, args.seed)
    benchmarks = run_benchmarks(corpus)
    write_csv(RESULTS / 'frequency_attack_raw.csv', frequency)
    write_csv(RESULTS / 'known_plaintext_raw.csv', known)
    write_csv(RESULTS / 'attack_summary.csv', summary)
    write_csv(RESULTS / 'known_prefix_lengths.csv', prefixes)
    write_csv(RESULTS / 'performance.csv', benchmarks)
    make_charts(summary, benchmarks)
    sample_plain = 'MEETATTHELIBRARYATSIXPM'
    sample_key, sample_hill = KEYS[0]
    stage_one = vigenere_encrypt(sample_plain, sample_key)
    sample_cipher = encrypt(sample_plain, sample_key, sample_hill)
    metadata = {'seed': args.seed, 'trials_per_configuration': args.trials, 'key_lengths': sorted({len(key) for key, _ in KEYS}), 'hill_key_length': 4, 'known_prefix_length': KNOWN_PREFIX, 'prefix_lengths': list(PREFIX_LENGTHS), 'maximum_key_length': 20, 'period_shortlist': 4, 'row_shortlist': 6, 'training_source': 'Pride and Prejudice + Sherlock Holmes', 'evaluation_source': 'A Tale of Two Cities (separate from training)', 'sample': {'plaintext': sample_plain, 'key': sample_key, 'hill_key': sample_hill, 'hill_matrix': hill_matrix(sample_hill), 'vigenere_stage': stage_one, 'ciphertext': sample_cipher, 'decrypted': decrypt(sample_cipher, sample_key, sample_hill)}}
    (RESULTS / 'experiment_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f'Results written to {RESULTS}')
if __name__ == '__main__':
    main()
