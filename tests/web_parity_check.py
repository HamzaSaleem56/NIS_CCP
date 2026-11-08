from __future__ import annotations
import json
import random
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from attack import QuadgramModel, frequency_attack, known_plaintext_attack
from cipher import decrypt, encrypt, hill_matrix, normalize
NODE_SCRIPT = """
const fs = require('fs');
global.self = global;
require(process.argv[1] + '/quadgrams.js');
const VHC = require(process.argv[1] + '/vhc.js');
const model = new VHC.QuadgramModel(self.VHC_QUADGRAMS.packed, self.VHC_QUADGRAMS.total);
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = cases.map((c) => {
  const ct = VHC.encrypt(c.plaintext, c.key, c.hill);
  const f = VHC.frequencyAttack(ct, model);
  const k = VHC.knownPlaintextAttack(c.plaintext.slice(0, c.prefix), ct, model);
  return { ct, pt: VHC.decrypt(ct, c.key, c.hill), score: model.score(c.plaintext), freq: [f.plaintext, f.key, f.hillKey, f.keyLength, f.evaluatedCandidates], known: [k.plaintext, k.key, k.hillKey, k.keyLength, k.evaluatedCandidates] };
});
process.stdout.write(JSON.stringify(out));
"""

@unittest.skipUnless(shutil.which('node'), 'Node.js is needed to test the web version')
class WebParityTests(unittest.TestCase):

    def test_web_version_matches_python(self):
        rng = random.Random(7)
        corpus = normalize((ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8'))
        hill_keys = ('HILL', 'JUMP', 'RUSH', 'LAMB', 'BOLT', 'FERN', 'REEF', 'VOLT', 'HYMN', 'JOLT')
        cases = []
        for i in range(24):
            length = (101, 200, 400, 801)[i % 4]
            start = rng.randrange(len(corpus) - length)
            key = ''.join((chr(65 + rng.randrange(26)) for _ in range(rng.randrange(10, 16))))
            cases.append({'plaintext': corpus[start:start + length], 'key': key, 'hill': hill_keys[i % len(hill_keys)], 'prefix': 40})
        result = subprocess.run(['node', '-e', NODE_SCRIPT, str(ROOT / 'docs')], input=json.dumps(cases), capture_output=True, text=True, check=True)
        web = json.loads(result.stdout)
        model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
        for case, js in zip(cases, web):
            ciphertext = encrypt(case['plaintext'], case['key'], case['hill'])
            self.assertEqual(js['ct'], ciphertext)
            self.assertEqual(js['pt'], decrypt(ciphertext, case['key'], case['hill']))
            self.assertAlmostEqual(js['score'], model.score(case['plaintext']), places=9)
            f = frequency_attack(ciphertext, model)
            self.assertEqual(js['freq'], [f.plaintext, f.key, f.hill_key, f.key_length, f.evaluated_candidates])
            k = known_plaintext_attack(case['plaintext'][:case['prefix']], ciphertext, model)
            self.assertEqual(js['known'], [k.plaintext, k.key, k.hill_key, k.key_length, k.evaluated_candidates])
if __name__ == '__main__':
    unittest.main()
