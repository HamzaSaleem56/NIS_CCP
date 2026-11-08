(function (root) {
  'use strict';

  const ENGLISH_FREQUENCIES = [0.082, 0.015, 0.028, 0.043, 0.127, 0.022, 0.02, 0.061, 0.07, 0.0015, 0.0077, 0.04, 0.024, 0.067, 0.075, 0.019, 0.00095, 0.06, 0.063, 0.091, 0.028, 0.0098, 0.024, 0.0015, 0.02, 0.00074];
  const MIN_KEY_LENGTH = 10;
  const HILL_KEY_LENGTH = 4;

  function gcd(a, b) {
    a = Math.abs(a); b = Math.abs(b);
    while (b) { [a, b] = [b, a % b]; }
    return a;
  }
  const mod = (x) => ((x % 26) + 26) % 26;
  const UNITS = [];
  for (let k = 1; k < 26; k++) if (gcd(k, 26) === 1) UNITS.push(k);

  function fsum(values) {
    let s = 0, c = 0;
    for (const x of values) {
      const t = s + x;
      if (Math.abs(s) >= Math.abs(x)) c += (s - t) + x; else c += (x - t) + s;
      s = t;
    }
    return s + c;
  }

  function normalize(text) {
    let out = '';
    for (const ch of String(text)) {
      const code = ch.charCodeAt(0);
      if (ch.length === 1 && code < 128 && /[A-Za-z]/.test(ch)) out += ch.toUpperCase();
    }
    return out;
  }

  class CipherError extends Error {}

  function validateKey(key, minimum = MIN_KEY_LENGTH) {
    const normalized = normalize(key);
    if (normalized.length < minimum) throw new CipherError(`The keyword needs at least ${minimum} letters (A–Z). It has ${normalized.length}.`);
    return normalized;
  }

  const shiftChar = (ch, amount) => String.fromCharCode(mod(ch.charCodeAt(0) - 65 + amount) + 65);

  function vigenereEncrypt(plaintext, key) {
    const text = normalize(plaintext);
    const shifts = [...validateKey(key, 1)].map((c) => c.charCodeAt(0) - 65);
    let out = '';
    for (let i = 0; i < text.length; i++) out += shiftChar(text[i], shifts[i % shifts.length]);
    return out;
  }

  function vigenereDecrypt(ciphertext, key) {
    const text = normalize(ciphertext);
    const shifts = [...validateKey(key, 1)].map((c) => c.charCodeAt(0) - 65);
    let out = '';
    for (let i = 0; i < text.length; i++) out += shiftChar(text[i], -shifts[i % shifts.length]);
    return out;
  }

  const determinant = (m) => mod(m[0][0] * m[1][1] - m[0][1] * m[1][0]);
  const isInvertible = (m) => gcd(determinant(m), 26) === 1;

  function modInverse(a) {
    for (let x = 1; x < 26; x++) if ((a * x) % 26 === 1) return x;
    throw new CipherError('No inverse mod 26');
  }

  function matrixInverse(m) {
    const det = determinant(m);
    if (gcd(det, 26) !== 1) throw new CipherError('This Hill matrix cannot be inverted mod 26.');
    const d = modInverse(det);
    const [[a, b], [c, e]] = m;
    return [[mod(e * d), mod(-b * d)], [mod(-c * d), mod(a * d)]];
  }

  function hillCheck(hillKey) {
    const normalized = normalize(hillKey);
    if (normalized.length !== HILL_KEY_LENGTH) return { ok: false, normalized, reason: `The Hill key needs exactly 4 letters (A–Z). It has ${normalized.length}.` };
    const v = [...normalized].map((c) => c.charCodeAt(0) - 65);
    const matrix = [[v[0], v[1]], [v[2], v[3]]];
    const det = determinant(matrix);
    if (gcd(det, 26) !== 1) {
      const why = det % 2 === 0 ? (det === 0 ? 'it is 0' : 'it is even') : 'it is 13';
      return { ok: false, normalized, matrix, det, reason: `${normalized} gives determinant ${det}, and ${why}, so it cannot be undone. The determinant must be odd and not 13.` };
    }
    return { ok: true, normalized, matrix, det, inverse: matrixInverse(matrix), detInverse: modInverse(det) };
  }

  function hillMatrix(hillKey) {
    const check = hillCheck(hillKey);
    if (!check.ok) throw new CipherError(check.reason);
    return check.matrix;
  }

  function applyMatrix(text, m) {
    const [[a, b], [c, d]] = m;
    const paired = text.length - (text.length % 2);
    let out = '';
    for (let i = 0; i < paired; i += 2) {
      const x = text.charCodeAt(i) - 65, y = text.charCodeAt(i + 1) - 65;
      out += String.fromCharCode(mod(a * x + b * y) + 65) + String.fromCharCode(mod(c * x + d * y) + 65);
    }
    return out + text.slice(paired);
  }

  const hillEncrypt = (plaintext, hillKey) => applyMatrix(normalize(plaintext), hillMatrix(hillKey));
  const hillDecrypt = (ciphertext, hillKey) => applyMatrix(normalize(ciphertext), matrixInverse(hillMatrix(hillKey)));

  function encrypt(plaintext, key, hillKey) {
    hillMatrix(hillKey);
    return hillEncrypt(vigenereEncrypt(plaintext, validateKey(key)), hillKey);
  }

  function decrypt(ciphertext, key, hillKey) {
    const k = validateKey(key);
    return vigenereDecrypt(hillDecrypt(ciphertext, hillKey), k);
  }

  function randomHillKey(rng = Math.random) {
    for (;;) {
      let s = '';
      for (let i = 0; i < 4; i++) s += String.fromCharCode(65 + Math.floor(rng() * 26));
      if (hillCheck(s).ok) return s;
    }
  }

  function randomKeyword(length = 12, rng = Math.random) {
    let s = '';
    for (let i = 0; i < length; i++) s += String.fromCharCode(65 + Math.floor(rng() * 26));
    return s;
  }

  class QuadgramModel {
    constructor(packed, total) {
      this.total = total;
      this.denominator = total + 0.1 * Math.pow(26, 4);
      this.unknown = Math.log10(0.1 / this.denominator);
      this.table = new Map();
      for (const item of packed.split(' ')) {
        if (!item) continue;
        this.table.set(item.slice(0, 4), Math.log10((Number(item.slice(4)) + 0.1) / this.denominator));
      }
    }
    score(text) {
      const n = normalize(text);
      if (n.length < 4) return -100.0;
      const values = new Array(n.length - 3);
      for (let i = 0; i < n.length - 3; i++) {
        const v = this.table.get(n.slice(i, i + 4));
        values[i] = v === undefined ? this.unknown : v;
      }
      return fsum(values) / (n.length - 3);
    }
  }

  function indexOfCoincidence(values) {
    const n = values.length;
    if (n < 2) return 0.0;
    const counts = new Map();
    for (const v of values) counts.set(v, (counts.get(v) || 0) + 1);
    let total = 0;
    for (const c of counts.values()) total += c * (c - 1);
    return total / (n * (n - 1));
  }

  function canonicalRow(a, b) {
    let best = null;
    for (const k of UNITS) {
      const r = [(k * a) % 26, (k * b) % 26];
      if (best === null || r[0] < best[0] || (r[0] === best[0] && r[1] < best[1])) best = r;
    }
    return best;
  }

  const ROW_CLASSES = (() => {
    const seen = new Map();
    for (let a = 0; a < 26; a++) for (let b = 0; b < 26; b++) {
      if (gcd(gcd(a, b), 26) !== 1) continue;
      const r = canonicalRow(a, b);
      seen.set(r[0] * 26 + r[1], r);
    }
    return [...seen.keys()].sort((x, y) => x - y).map((k) => seen.get(k));
  })();

  const blockPeriod = (L) => L / gcd(L, 2);
  const stride = (arr, start, step) => { const out = []; for (let i = start; i < arr.length; i += step) out.push(arr[i]); return out; };

  function histogram(values) {
    const h = new Array(26).fill(0);
    for (const v of values) h[v] += 1;
    return h;
  }

  function bestShift(h) {
    let n = 0;
    for (const v of h) n += v;
    if (!n) return [0, 0.0];
    let best = [0, Infinity];
    const terms = new Array(26);
    for (let shift = 0; shift < 26; shift++) {
      for (let i = 0; i < 26; i++) { const o = h[(i + shift) % 26]; terms[i] = (o * o) / ENGLISH_FREQUENCIES[i]; }
      const chi = fsum(terms) / n - n;
      if (chi < best[1]) best = [shift, chi];
    }
    return best;
  }

  function scaled(h, unit) {
    const out = new Array(26).fill(0);
    for (let v = 0; v < 26; v++) out[(v * unit) % 26] += h[v];
    return out;
  }

  function keyFromShifts(first, second, L) {
    const key = new Array(L).fill(0);
    for (let r = 0; r < first.length; r++) { key[(2 * r) % L] = first[r]; key[(2 * r + 1) % L] = second[r]; }
    return key.map((v) => String.fromCharCode(65 + v)).join('');
  }

  function decryptWith(codes, inv, first, second) {
    const [[a, b], [c, d]] = inv;
    const period = first.length;
    const paired = codes.length - (codes.length % 2);
    let out = '';
    for (let i = 0; i < paired; i += 2) {
      const r = (i / 2) % period, x = codes[i], y = codes[i + 1];
      out += String.fromCharCode(mod(a * x + b * y - first[r]) + 65) + String.fromCharCode(mod(c * x + d * y - second[r]) + 65);
    }
    if (paired < codes.length) out += String.fromCharCode(mod(codes[codes.length - 1] - first[(paired / 2) % period]) + 65);
    return out;
  }

  function hillKeyFromInverse(inv) {
    const m = matrixInverse(inv);
    return [m[0][0], m[0][1], m[1][0], m[1][1]].map((v) => String.fromCharCode(65 + v)).join('');
  }

  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
  const emptyResult = () => ({ candidateFound: false, plaintext: '', key: '', hillKey: '', keyLength: 0, score: -100.0, evaluatedCandidates: 0, elapsedMs: 0 });
  const cmpRow = (p, q) => (p[0] - q[0]) || (p[1] - q[1]);

  function frequencyAttack(ciphertext, model, opts = {}) {
    const maxKeyLength = opts.maxKeyLength ?? 20, periodShortlist = opts.periodShortlist ?? 4, rowShortlist = opts.rowShortlist ?? 6, multiplesKept = opts.multiplesKept ?? 2;
    const started = now();
    const codes = [...normalize(ciphertext)].map((c) => c.charCodeAt(0) - 65);
    let best = emptyResult();
    if (codes.length < 4) { best.elapsedMs = now() - started; return best; }
    const usableLength = codes.length - (codes.length % 2);
    const xs = [], ys = [];
    for (let i = 0; i < usableLength; i += 2) { xs.push(codes[i]); ys.push(codes[i + 1]); }
    const projections = new Map();
    for (const row of ROW_CLASSES) projections.set(row, xs.map((x, j) => (row[0] * x + row[1] * ys[j]) % 26));
    const periodRankings = [];
    for (let L = MIN_KEY_LENGTH; L <= maxKeyLength; L++) {
      const period = blockPeriod(L);
      if (period > xs.length) continue;
      const ranked = [];
      for (const [row, values] of projections) {
        const usable = [];
        for (let r = 0; r < period; r++) { const col = stride(values, r, period); if (col.length > 1) usable.push(col); }
        const ic = usable.length ? fsum(usable.map(indexOfCoincidence)) / usable.length : 0.0;
        ranked.push([-ic, row]);
      }
      ranked.sort((p, q) => (p[0] - q[0]) || cmpRow(p[1], q[1]));
      periodRankings.push([ranked[0][0] + ranked[1][0], L, period, ranked.slice(0, rowShortlist).map((x) => x[1])]);
    }
    periodRankings.sort((p, q) => (p[0] - q[0]) || (p[1] - q[1]));
    let evaluations = 0;
    for (const [, L, period, rows] of periodRankings.slice(0, periodShortlist)) {
      const options = new Map();
      for (const row of rows) {
        const hists = [];
        for (let r = 0; r < period; r++) hists.push(histogram(stride(projections.get(row), r, period)));
        const scoredList = [];
        for (const unit of UNITS) {
          const shifts = [], chis = [];
          for (const h of hists) { const [s, chi] = bestShift(scaled(h, unit)); shifts.push(s); chis.push(chi); }
          let total = 0.0;
          for (const chi of chis) total += chi;
          scoredList.push([total, [(unit * row[0]) % 26, (unit * row[1]) % 26], shifts]);
        }
        scoredList.sort((p, q) => p[0] - q[0]);
        options.set(row, scoredList.slice(0, multiplesKept));
      }
      for (const r1 of rows) for (const r2 of rows) {
        if (r1 === r2) continue;
        for (const [, firstRow, firstShifts] of options.get(r1)) for (const [, secondRow, secondShifts] of options.get(r2)) {
          const inv = [firstRow, secondRow];
          if (!isInvertible(inv)) continue;
          const candidate = decryptWith(codes, inv, firstShifts, secondShifts);
          const score = model.score(candidate);
          evaluations += 1;
          if (score > best.score) best = { candidateFound: true, plaintext: candidate, key: keyFromShifts(firstShifts, secondShifts, L), hillKey: hillKeyFromInverse(inv), keyLength: L, score, evaluatedCandidates: 0, elapsedMs: 0 };
        }
      }
    }
    best.evaluatedCandidates = evaluations;
    best.elapsedMs = now() - started;
    return best;
  }

  function* combinations2(arr) {
    for (let i = 0; i < arr.length; i++) for (let j = i + 1; j < arr.length; j++) yield [arr[i], arr[j]];
  }

  function solveMatrix(differences) {
    const pool = differences.slice();
    const head = differences.slice(0, 12);
    for (const [[p1, c1], [p2, c2]] of combinations2(head)) pool.push([[p1[0] + p2[0], p1[1] + p2[1]], [c1[0] + c2[0], c1[1] + c2[1]]]);
    for (const [[p1, c1], [p2, c2]] of combinations2(pool)) {
      const plain = [[mod(p1[0]), mod(p2[0])], [mod(p1[1]), mod(p2[1])]];
      if (!isInvertible(plain)) continue;
      const inv = matrixInverse(plain);
      const cm = [[mod(c1[0]), mod(c2[0])], [mod(c1[1]), mod(c2[1])]];
      return [0, 1].map((i) => [0, 1].map((j) => (cm[i][0] * inv[0][j] + cm[i][1] * inv[1][j]) % 26));
    }
    return null;
  }

  function knownPlaintextAttack(knownPrefix, ciphertext, model, opts = {}) {
    const maxKeyLength = opts.maxKeyLength ?? 20;
    const started = now();
    const known = [...normalize(knownPrefix)].map((c) => c.charCodeAt(0) - 65);
    const codes = [...normalize(ciphertext)].map((c) => c.charCodeAt(0) - 65);
    let best = emptyResult();
    if (known.length > codes.length) { best.elapsedMs = now() - started; return best; }
    const kb = Math.floor(known.length / 2);
    const plainBlocks = [], cipherBlocks = [];
    for (let j = 0; j < kb; j++) { plainBlocks.push([known[2 * j], known[2 * j + 1]]); cipherBlocks.push([codes[2 * j], codes[2 * j + 1]]); }
    const knownText = known.map((v) => String.fromCharCode(65 + v)).join('');
    let evaluations = 0;
    for (let L = MIN_KEY_LENGTH; L <= maxKeyLength; L++) {
      const period = blockPeriod(L);
      if (kb < period) continue;
      const diffs = [];
      for (let r = 0; r < period; r++) {
        const members = [];
        for (let j = r; j < kb; j += period) members.push(j);
        for (const [i, j] of combinations2(members)) diffs.push([[plainBlocks[i][0] - plainBlocks[j][0], plainBlocks[i][1] - plainBlocks[j][1]], [cipherBlocks[i][0] - cipherBlocks[j][0], cipherBlocks[i][1] - cipherBlocks[j][1]]]);
      }
      const m = solveMatrix(diffs);
      if (m === null || !isInvertible(m)) continue;
      const [[a, b], [c, d]] = m;
      if (diffs.some(([p, q]) => mod(a * p[0] + b * p[1] - q[0]) || mod(c * p[0] + d * p[1] - q[1]))) continue;
      const inv = matrixInverse(m);
      const first = [], second = [];
      let consistent = true;
      for (let r = 0; r < period && consistent; r++) {
        const offsets = new Set();
        for (let j = r; j < kb; j += period) {
          const [x, y] = cipherBlocks[j];
          offsets.add(`${mod(inv[0][0] * x + inv[0][1] * y - plainBlocks[j][0])},${mod(inv[1][0] * x + inv[1][1] * y - plainBlocks[j][1])}`);
        }
        if (offsets.size !== 1) { consistent = false; break; }
        const [o1, o2] = [...offsets][0].split(',').map(Number);
        first.push(o1); second.push(o2);
      }
      if (!consistent) continue;
      const candidate = decryptWith(codes, inv, first, second);
      evaluations += 1;
      if (candidate.slice(0, known.length) !== knownText) continue;
      const score = model.score(candidate);
      if (score > best.score) best = { candidateFound: true, plaintext: candidate, key: keyFromShifts(first, second, L), hillKey: hillKeyFromInverse(inv), keyLength: L, score, evaluatedCandidates: 0, elapsedMs: 0 };
    }
    best.evaluatedCandidates = evaluations;
    best.elapsedMs = now() - started;
    return best;
  }

  const api = {
    MIN_KEY_LENGTH, CipherError, normalize, validateKey, vigenereEncrypt, vigenereDecrypt, determinant, isInvertible, matrixInverse,
    hillCheck, hillMatrix, hillEncrypt, hillDecrypt, encrypt, decrypt, randomHillKey, randomKeyword, QuadgramModel,
    frequencyAttack, knownPlaintextAttack, mod,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.VHC = api;
})(typeof self !== 'undefined' ? self : this);
