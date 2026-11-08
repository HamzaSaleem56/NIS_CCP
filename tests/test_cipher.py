from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from attack import QuadgramModel, frequency_attack, known_plaintext_attack
from cipher import decrypt, encrypt, hill_decrypt, hill_encrypt, hill_matrix, matrix_inverse, normalize, shift_decrypt, shift_encrypt, vigenere_decrypt, vigenere_encrypt

class CipherTests(unittest.TestCase):

    def test_normalization(self):
        self.assertEqual(normalize('Attack at Dawn! 123'), 'ATTACKATDAWN')
        self.assertEqual(normalize(''), '')
        self.assertEqual(normalize('AßıB'), 'AB')

    def test_standard_vigenere_vector(self):
        self.assertEqual(vigenere_encrypt('ATTACKATDAWN', 'LEMON'), 'LXFOPVEFRNHR')
        self.assertEqual(vigenere_decrypt('LXFOPVEFRNHR', 'LEMON'), 'ATTACKATDAWN')

    def test_standard_hill_vector(self):
        self.assertEqual(hill_matrix('HILL'), ((7, 8), (11, 11)))
        self.assertEqual(matrix_inverse(hill_matrix('HILL')), ((25, 22), (1, 23)))
        self.assertEqual(hill_encrypt('SHORTEXAMPLE', 'HILL'), 'APADJTFTWLFJ')
        self.assertEqual(hill_decrypt('APADJTFTWLFJ', 'HILL'), 'SHORTEXAMPLE')

    def test_hill_round_trips_including_odd_lengths(self):
        for hill_key in ('HILL', 'JUMP', 'RUSH', 'LAMB'):
            for length in range(80):
                text = ''.join((chr(65 + (i * 7 + 3) % 26) for i in range(length)))
                encrypted = hill_encrypt(text, hill_key)
                self.assertEqual(len(encrypted), length)
                self.assertEqual(hill_decrypt(encrypted, hill_key), text)

    def test_custom_cipher_round_trips(self):
        base = 'THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG'
        for key, hill_key in (('CRYPTOGRAPHY', 'HILL'), ('KERCKHOFFS', 'JUMP'), ('INFORMATION', 'LAMB')):
            for length in (0, 1, 2, 3, 7, 10, 11, 12, 35, 101, 1001):
                text = (base * 40)[:length]
                ciphertext = encrypt(text, key, hill_key)
                self.assertEqual(len(ciphertext), length)
                self.assertEqual(decrypt(ciphertext, key, hill_key), text)

    def test_key_validation(self):
        with self.assertRaises(ValueError):
            encrypt('TEST', 'SHORT', 'HILL')
        with self.assertRaises(ValueError):
            decrypt('TEST', '1234567890', 'HILL')
        for bad_hill_key in ('AAAA', 'ABCD', 'HIL', 'HILLS'):
            with self.assertRaises(ValueError):
                encrypt('TEST', 'CRYPTOGRAPHY', bad_hill_key)

    def test_shift_baseline(self):
        text = 'MEETMEATTHEGATES'
        self.assertEqual(shift_decrypt(shift_encrypt(text, 3), 3), text)

    def test_known_prefix_recovers_full_message(self):
        model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
        evaluation = (ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8')
        plaintext = normalize(evaluation[1000:1801])
        ciphertext = encrypt(plaintext, 'CRYPTOGRAPHY', 'HILL')
        result = known_plaintext_attack(plaintext[:32], ciphertext, model)
        self.assertTrue(result.candidate_found)
        self.assertEqual(result.plaintext, plaintext)
        self.assertEqual(result.hill_key, 'HILL')

    def test_frequency_attack_recovers_long_message(self):
        model = QuadgramModel(ROOT / 'data' / 'english_corpus.txt')
        evaluation = (ROOT / 'data' / 'evaluation_corpus.txt').read_text(encoding='utf-8')
        plaintext = normalize(evaluation[5000:7000])
        ciphertext = encrypt(plaintext, 'CRYPTOGRAPHY', 'HILL')
        result = frequency_attack(ciphertext, model)
        self.assertEqual(result.plaintext, plaintext)
        self.assertEqual(result.key, 'CRYPTOGRAPHY')
        self.assertEqual(result.hill_key, 'HILL')
if __name__ == '__main__':
    unittest.main()
