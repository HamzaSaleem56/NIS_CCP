from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from cipher import normalize
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SAMPLES = (('Dickens, passage 1', 2000), ('Dickens, passage 2', 200000), ('Dickens, passage 3', 600000))

def main() -> None:
    DOCS.mkdir(exist_ok=True)
    training = normalize((ROOT / 'data' / 'english_corpus.txt').read_text(encoding='utf-8'))
    counts = Counter((training[i:i + 4] for i in range(len(training) - 3)))
    packed = ' '.join((f'{gram}{count}' for gram, count in sorted(counts.items())))
    (DOCS / 'quadgrams.js').write_text(f'self.VHC_QUADGRAMS = {json.dumps({'total': sum(counts.values()), 'packed': packed})};\n', encoding='utf-8')
    evaluation = normalize((ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8'))
    samples = [{'title': title, 'text': evaluation[start:start + 3200]} for title, start in SAMPLES]
    (DOCS / 'samples.js').write_text(f'self.VHC_SAMPLES = {json.dumps(samples)};\n', encoding='utf-8')
    print(f'quadgrams: {len(counts)} entries; samples: {len(samples)}')
if __name__ == '__main__':
    main()
