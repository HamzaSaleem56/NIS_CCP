from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from attack import QuadgramModel, frequency_attack, known_plaintext_attack
from cipher import decrypt, derive_rails, encrypt, normalize, rail_fence_decrypt, rail_fence_encrypt, shift_decrypt, shift_encrypt, vigenere_decrypt, vigenere_encrypt

class CipherTests(unittest.TestCase):

    def test_normalization(self):
        self.assertEqual(normalize('Attack at Dawn! 123'), 'ATTACKATDAWN')
        self.assertEqual(normalize(''), '')
        self.assertEqual(normalize('AßıB'), 'AB')

    def test_standard_vigenere_vector(self):
        self.assertEqual(vigenere_encrypt('ATTACKATDAWN', 'LEMON'), 'LXFOPVEFRNHR')
        self.assertEqual(vigenere_decrypt('LXFOPVEFRNHR', 'LEMON'), 'ATTACKATDAWN')

    def test_rail_fence_round_trips(self):
        for rails in range(2, 9):
            for length in range(80):
                text = ''.join((chr(65 + (i * 7 + 3) % 26) for i in range(length)))
                encrypted = rail_fence_encrypt(text, rails)
                self.assertEqual(rail_fence_decrypt(encrypted, rails), text)

    def test_custom_cipher_round_trips(self):
        base = 'THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG'
        for key in ('CRYPTOGRAPHY', 'KERCKHOFFS', 'SUBSTITUTION'):
            for length in (0, 1, 2, 3, 7, 10, 11, 12, 35, 101, 1001):
                text = (base * 40)[:length]
                ciphertext = encrypt(text, key)
                self.assertEqual(decrypt(ciphertext, key), text)

    def test_key_validation_and_rail_derivation(self):
        with self.assertRaises(ValueError):
            encrypt('TEST', 'SHORT')
        with self.assertRaises(ValueError):
            encrypt('', 'CRYPTOGRAPHY', 1)
        with self.assertRaises(ValueError):
            decrypt('', 'CRYPTOGRAPHY', 9)
        with self.assertRaises(ValueError):
            decrypt('TEST', '1234567890')
        for key in ('CRYPTOGRAPHY', 'KERCKHOFFS', 'SUBSTITUTION'):
            self.assertIn(derive_rails(key), range(2, 9))

    def test_shift_baseline(self):
        text = 'MEETMEATTHEGATES'
        self.assertEqual(shift_decrypt(shift_encrypt(text, 3), 3), text)

    def test_known_prefix_recovers_full_message(self):
        model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
        evaluation = (ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8')
        plaintext = normalize(evaluation[1000:1800])
        key = 'CRYPTOGRAPHY'
        ciphertext = encrypt(plaintext, key)
        result = known_plaintext_attack(plaintext[:24], ciphertext, model)
        self.assertTrue(result.candidate_found)
        self.assertEqual(result.plaintext, plaintext)
        self.assertEqual(result.rails, derive_rails(key))

    def test_frequency_attack_recovers_long_message(self):
        model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
        evaluation = (ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8')
        plaintext = normalize(evaluation[5000:7000])
        key = 'CRYPTOGRAPHY'
        ciphertext = encrypt(plaintext, key)
        result = frequency_attack(ciphertext, model)
        self.assertEqual(result.plaintext, plaintext)
        self.assertEqual(result.key, key)
        self.assertEqual(result.rails, derive_rails(key))
if __name__ == '__main__':
    unittest.main()
