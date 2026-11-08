(function () {
  'use strict';
  const V = window.VHC;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const letter = (n) => String.fromCharCode(65 + n);
  const num = (ch) => ch.charCodeAt(0) - 65;
  let model = null;
  const getModel = () => (model ||= new V.QuadgramModel(window.VHC_QUADGRAMS.packed, window.VHC_QUADGRAMS.total));

  const TABS = ['encrypt', 'break', 'keys', 'about'];
  function showTab(name, focus) {
    if (!TABS.includes(name)) name = 'encrypt';
    for (const t of TABS) {
      const tab = $('tab-' + t), panel = $('panel-' + t), on = t === name;
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      panel.hidden = !on;
    }
    if (focus) $('tab-' + name).focus();
    if (location.hash !== '#' + name) history.replaceState(null, '', '#' + name);
  }
  document.querySelectorAll('.tabs button').forEach((b, i, all) => {
    b.addEventListener('click', () => { showTab(b.dataset.tab); window.scrollTo({ top: 0 }); });
    b.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const next = all[(i + (e.key === 'ArrowRight' ? 1 : all.length - 1)) % all.length];
      showTab(next.dataset.tab, true);
    });
  });
  window.addEventListener('hashchange', () => showTab(location.hash.slice(1)));
  document.querySelector('.brand').addEventListener('click', (e) => { e.preventDefault(); showTab('encrypt'); });

  const matrixHtml = (m, extra = '') => `<span class="matrix ${extra}" style="--cols:${m[0].length}">${m.flat().map((v) => `<span>${esc(v)}</span>`).join('')}</span>`;
  const columnHtml = (vals, extra = '') => matrixHtml(vals.map((v) => [v]), extra);

  const mode = () => document.querySelector('input[name="mode"]:checked').value;

  function keywordStatus() {
    const k = V.normalize($('keyword').value), el = $('keyword-status');
    const ok = k.length >= V.MIN_KEY_LENGTH;
    el.textContent = ok ? `${k.length} letters, good.` : `Needs at least 10 letters; it has ${k.length}.`;
    el.className = 'status ' + (ok ? 'ok' : 'bad');
    $('keyword').setAttribute('aria-invalid', String(!ok));
    return ok;
  }
  function hillStatus() {
    const c = V.hillCheck($('hillkey').value), el = $('hill-status');
    if (c.ok) el.textContent = `Determinant ${c.det}, so it can be undone.`;
    else if (c.normalized.length !== 4) el.textContent = `Needs exactly 4 letters; it has ${c.normalized.length}.`;
    else el.textContent = `Determinant ${c.det} can't be undone. Try the Hill keys tab.`;
    el.className = 'status ' + (c.ok ? 'ok' : 'bad');
    $('hillkey').setAttribute('aria-invalid', String(!c.ok));
    return c.ok;
  }

  function syncMode() {
    const enc = mode() === 'encrypt';
    $('run-cipher').textContent = enc ? 'Encrypt message' : 'Decrypt message';
    $('msg-label').textContent = enc ? 'Message' : 'Ciphertext';
    $('result-label').textContent = enc ? 'Ciphertext' : 'Decrypted message';
    $('send-to-break').hidden = !enc;
    $('cipher-result').hidden = true;
    $('steps').hidden = true;
  }
  document.querySelectorAll('input[name="mode"]').forEach((r) => r.addEventListener('change', syncMode));
  $('keyword').addEventListener('input', keywordStatus);
  $('hillkey').addEventListener('input', hillStatus);

  let last = null;
  function runCipher() {
    const err = $('cipher-error');
    err.hidden = true;
    const enc = mode() === 'encrypt';
    const text = V.normalize($('message').value);
    try {
      if (!text) throw new V.CipherError(`Type a ${enc ? 'message' : 'ciphertext'} with at least one letter A–Z.`);
      const key = V.validateKey($('keyword').value);
      const hill = V.hillCheck($('hillkey').value);
      if (!hill.ok) throw new V.CipherError(hill.reason);
      const out = enc ? V.encrypt(text, key, hill.normalized) : V.decrypt(text, key, hill.normalized);
      last = { enc, input: text, key, hill, out };
      $('result-text').textContent = out;
      $('cipher-result').hidden = false;
      renderSteps();
    } catch (e) {
      err.textContent = e.message;
      err.hidden = false;
      $('cipher-result').hidden = true;
      $('steps').hidden = true;
    }
  }
  $('run-cipher').addEventListener('click', runCipher);
  $('message').addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runCipher(); });

  $('random-keys').addEventListener('click', () => {
    $('keyword').value = V.randomKeyword(10 + Math.floor(Math.random() * 5));
    $('hillkey').value = V.randomHillKey();
    keywordStatus(); hillStatus();
  });
  $('load-example').addEventListener('click', () => {
    document.querySelector('input[name="mode"][value="encrypt"]').checked = true;
    syncMode();
    $('message').value = 'Meet at the library at six pm';
    $('keyword').value = 'CRYPTOGRAPHY';
    $('hillkey').value = 'HILL';
    keywordStatus(); hillStatus();
    runCipher();
  });
  $('copy-result').addEventListener('click', async () => {
    const b = $('copy-result');
    try { await navigator.clipboard.writeText($('result-text').textContent); b.textContent = 'Copied'; }
    catch { b.textContent = 'Select and copy'; }
    setTimeout(() => { b.textContent = 'Copy'; }, 1500);
  });

  const SHOW = 36;
  function tableau(rows, outIndex) {
    const n = rows[0][1].length, shown = Math.min(n, SHOW);
    const body = rows.map(([label, s], r) => {
      const cells = [...s.slice(0, shown)].map((c) => `<td>${esc(c)}</td>`).join('');
      const more = n > shown && r === 0 ? `<td class="more" rowspan="${rows.length}">+${n - shown} more</td>` : '';
      return `<tr class="${r === outIndex ? 'out' : ''}"><th scope="row">${esc(label)}</th>${cells}${more}</tr>`;
    }).join('');
    return `<table>${body}</table>`;
  }

  let pairState = null;
  function renderSteps() {
    const { enc, input, key, hill, out } = last;
    const H = hill.matrix, Hi = hill.inverse;
    const repeated = [...input].map((_, i) => key[i % key.length]).join('');
    $('step-clean').textContent = input;
    $('step-result').textContent = out;
    $('step-odd').hidden = input.length % 2 === 0;
    const list = document.querySelector('.step-list');
    const vigLi = $('step-vig').closest('li'), hillLi = $('step-pairs').closest('li');
    if (enc) {
      list.insertBefore(vigLi, hillLi);
      const T = V.vigenereEncrypt(input, key);
      $('step-vig-title').textContent = 'Stage I: Vigenère';
      $('step-vig-help').textContent = 'Each letter moves forward by the matching keyword letter (A = 0, B = 1, …). The keyword repeats.';
      $('step-vig').innerHTML = tableau([['Message', input], ['Keyword', repeated], ['Shifted', T]], 2);
      $('step-hill-title').textContent = 'Stage II: Hill, two letters at a time';
      $('step-hill-help').textContent = 'Each pair becomes a column of two numbers and is multiplied by the key matrix, mod 26. Pick a pair to see the maths.';
      pairState = { from: T, to: out, M: H, label: 'H' };
    } else {
      list.insertBefore(hillLi, vigLi);
      const T = V.hillDecrypt(input, hill.normalized);
      $('step-hill-title').textContent = 'Undo Stage II: inverse Hill matrix';
      $('step-hill-help').textContent = `Each pair is multiplied by the inverse matrix H⁻¹, mod 26. For ${hill.normalized}, det = ${hill.det} and its inverse mod 26 is ${hill.detInverse}. Pick a pair to see the maths.`;
      $('step-vig-title').textContent = 'Undo Stage I: Vigenère';
      $('step-vig-help').textContent = 'Each letter moves back by the matching keyword letter.';
      $('step-vig').innerHTML = tableau([['After Hill⁻¹', T], ['Keyword', repeated], ['Message', out]], 2);
      pairState = { from: input, to: T, M: Hi, label: 'H⁻¹' };
    }
    renderPairs(0);
    $('steps').hidden = false;
  }

  function renderPairs(selected) {
    const { from, to } = pairState;
    const count = Math.ceil(from.length / 2), limit = Math.min(count, 60);
    let html = '';
    for (let j = 0; j < limit; j++) {
      const a = from.slice(2 * j, 2 * j + 2), single = a.length === 1;
      html += `<button role="option" data-j="${j}" aria-selected="${j === selected}" class="${single ? 'single' : ''}" title="Pair ${j + 1}">${esc(a)}</button>`;
    }
    if (count > limit) html += `<span class="note">+${count - limit} more pairs</span>`;
    $('step-pairs').innerHTML = html;
    $('step-pairs').querySelectorAll('button').forEach((b) => b.addEventListener('click', () => renderPairs(Number(b.dataset.j))));
    renderCalc(selected);
  }

  function renderCalc(j) {
    const { from, to, M, label } = pairState;
    const a = from.slice(2 * j, 2 * j + 2), b = to.slice(2 * j, 2 * j + 2);
    if (a.length === 1) {
      $('step-calc').innerHTML = `<p>${esc(a)} is the last letter and has no partner, so it skips the Hill stage and stays <strong class="mono">${esc(b)}</strong>.</p>`;
      return;
    }
    const x = num(a[0]), y = num(a[1]);
    const raw = [M[0][0] * x + M[0][1] * y, M[1][0] * x + M[1][1] * y];
    const res = raw.map((v) => V.mod(v));
    $('step-calc').innerHTML = `
      <div class="eq" aria-label="Pair ${j + 1} calculation">
        ${matrixHtml(M, 'big')}<span class="op">×</span>
        ${columnHtml([`${a[0]} ${x}`, `${a[1]} ${y}`])}<span class="op">=</span>
        ${columnHtml(raw)}<span class="op">mod 26 =</span>
        ${columnHtml([`${res[0]} ${letter(res[0])}`, `${res[1]} ${letter(res[1])}`], 'hl')}
      </div>
      <div class="calc-lines">
        <div>Top: ${M[0][0]}×${x} + ${M[0][1]}×${y} = ${raw[0]}, and ${raw[0]} mod 26 = ${res[0]} → ${letter(res[0])}</div>
        <div>Bottom: ${M[1][0]}×${x} + ${M[1][1]}×${y} = ${raw[1]}, and ${raw[1]} mod 26 = ${res[1]} → ${letter(res[1])}</div>
        <div>Pair ${j + 1}: ${esc(a)} becomes ${esc(b)} using ${label}.</div>
      </div>`;
  }

  const samples = window.VHC_SAMPLES || [];
  $('sample-pick').innerHTML = samples.map((s, i) => `<option value="${i}">${esc(s.title)}</option>`).join('');
  let truth = null;

  function setTruth(t) {
    truth = t;
    $('truth').hidden = !t;
    $('truth').open = false;
    $('known-auto').hidden = !t;
    $('known-manual').hidden = !!t;
    $('freq-out').innerHTML = '';
    $('known-out').innerHTML = '';
    if (t) {
      $('truth-key').textContent = t.key;
      $('truth-hill').textContent = t.hill;
      $('truth-text').textContent = t.plaintext;
      const max = Math.max(8, Math.min(96, t.plaintext.length - (t.plaintext.length % 2)));
      $('known-slider').max = String(max);
      $('known-slider').value = String(Math.min(knownChoice, max));
      updateKnownCount();
    }
  }

  $('make-secret').addEventListener('click', () => {
    const s = samples[Number($('sample-pick').value)];
    const plaintext = s.text.slice(0, Number($('sample-length').value));
    let key, hill;
    if ($('sample-keys').value === 'tool') {
      try {
        key = V.validateKey($('keyword').value);
        const c = V.hillCheck($('hillkey').value);
        if (!c.ok) throw new V.CipherError(c.reason);
        hill = c.normalized;
      } catch (e) {
        $('freq-out').innerHTML = '';
        $('known-out').innerHTML = '';
        $('attack-ct-help').textContent = `The keys on the Encrypt tab can't be used: ${e.message}`;
        $('attack-ct-help').className = 'help status bad';
        return;
      }
    } else {
      key = V.randomKeyword(10 + Math.floor(Math.random() * 5));
      hill = V.randomHillKey();
    }
    const ct = V.encrypt(plaintext, key, hill);
    $('attack-ct').value = ct;
    $('attack-ct-help').textContent = `${/^(8|11|18)/.test(String(ct.length)) ? 'An' : 'A'} ${ct.length}-letter secret message is ready. The attacker only sees this text.`;
    $('attack-ct-help').className = 'help';
    setTruth({ plaintext, key, hill, ct });
  });

  $('attack-ct').addEventListener('input', () => {
    if (truth && V.normalize($('attack-ct').value) !== truth.ct) {
      setTruth(null);
      $('attack-ct-help').textContent = 'Using your own ciphertext. The attacks will show their best guess, since the real message is unknown.';
      $('attack-ct-help').className = 'help';
    }
  });

  let knownChoice = 40;
  function updateKnownCount() { $('known-count').textContent = $('known-slider').value; }
  $('known-slider').addEventListener('input', () => { knownChoice = Number($('known-slider').value); updateKnownCount(); });

  function runLater(button, out, work) {
    const ct = V.normalize($('attack-ct').value);
    if (ct.length < 4) {
      out.innerHTML = '<p class="status bad">Make a secret message first, or paste a ciphertext of at least 4 letters.</p>';
      return;
    }
    button.disabled = true;
    out.innerHTML = '<p class="working">Working on it…</p>';
    setTimeout(() => {
      try { out.innerHTML = work(ct); } catch (e) { out.innerHTML = `<p class="status bad">${esc(e.message)}</p>`; }
      button.disabled = false;
    }, 40);
  }

  function diffHtml(guess, real) {
    const shown = 800;
    let html = '';
    for (let i = 0; i < Math.min(guess.length, shown); i++) {
      const c = esc(guess[i]);
      html += real && guess[i] !== real[i] ? `<span class="x">${c}</span>` : c;
    }
    if (guess.length > shown) html += ` … (+${guess.length - shown} letters)`;
    return html;
  }

  function resultHtml(r, extra) {
    if (!r.candidateFound) return `<p class="verdict bad">No answer found.</p><p>${extra.fail}</p><p class="note">Time: ${r.elapsedMs.toFixed(1)} ms, ${r.evaluatedCandidates} candidates checked.</p>`;
    let verdict, meter = '';
    if (truth) {
      let right = 0;
      for (let i = 0; i < truth.plaintext.length; i++) if (r.plaintext[i] === truth.plaintext[i]) right++;
      const pct = (100 * right) / truth.plaintext.length;
      const exact = r.plaintext === truth.plaintext;
      verdict = exact ? '<p class="verdict good">Broken. The whole message was recovered.</p>'
        : `<p class="verdict bad">Not broken. ${pct.toFixed(0)}% of letters are right.</p>`;
      meter = `<div class="meter" aria-hidden="true"><span style="width:${pct}%"></span></div>`;
      if (!exact && extra.hint) verdict += `<p class="note">${extra.hint}</p>`;
    } else {
      verdict = '<p class="verdict neutral">Best guess</p><p class="note">The real message is unknown, so read the text below to judge it.</p>';
    }
    const keyNote = truth && r.key !== truth.key && r.plaintext === truth.plaintext ? ' (the same key written twice, which decrypts identically)' : '';
    return `${verdict}${meter}
      <dl class="kv">
        <dt>Keyword found</dt><dd class="mono">${esc(r.key)}${keyNote ? `<span class="note">${keyNote}</span>` : ''}</dd>
        <dt>Hill key found</dt><dd class="mono">${esc(r.hillKey)}</dd>
        <dt>Time</dt><dd>${r.elapsedMs < 10 ? r.elapsedMs.toFixed(2) : r.elapsedMs.toFixed(0)} ms</dd>
        <dt>Candidates</dt><dd>${r.evaluatedCandidates} full ${r.evaluatedCandidates === 1 ? 'decryption' : 'decryptions'} checked</dd>
      </dl>
      <div class="recovered" aria-label="Recovered message${truth ? ', wrong letters marked' : ''}">${diffHtml(r.plaintext, truth && truth.plaintext)}</div>`;
  }

  $('run-freq').addEventListener('click', () => runLater($('run-freq'), $('freq-out'), (ct) => {
    const r = V.frequencyAttack(ct, getModel());
    return resultHtml(r, { fail: 'The ciphertext is too short to analyse.', hint: 'Short messages give too few letters per key position. Try 800 letters or more.' });
  }));

  $('run-known').addEventListener('click', () => runLater($('run-known'), $('known-out'), (ct) => {
    const known = truth ? truth.plaintext.slice(0, Number($('known-slider').value)) : V.normalize($('known-text').value);
    if (!known) throw new V.CipherError('Type the start of the message that the attacker knows.');
    const r = V.knownPlaintextAttack(known, ct, getModel());
    const head = `<p class="note">The attacker knew: <span class="mono">${esc(known)}</span></p>`;
    return head + resultHtml(r, { fail: `${known.length} known letters weren't enough to solve for the keys. A 10- or 12-letter keyword needs about 14–16 known letters; an odd-length keyword such as 11 or 13 letters needs about 2 × length + 4. Try more letters.` });
  }));

  $('send-to-break').addEventListener('click', () => {
    if (!last || !last.enc) return;
    $('attack-ct').value = last.out;
    setTruth({ plaintext: last.input, key: last.key, hill: last.hill.normalized, ct: last.out });
    $('attack-ct-help').textContent = `Your ${last.out.length}-letter ciphertext is loaded. Short messages are hard to break without known text; try the known-plaintext attack.`;
    $('attack-ct-help').className = 'help';
    showTab('break');
    window.scrollTo({ top: 0 });
  });

  const WORDS = ['HILL', 'JUMP', 'RUSH', 'LAMB', 'BOLT', 'FERN', 'REEF', 'VOLT', 'HYMN', 'JOLT', 'CODE', 'LOCK', 'SAFE', 'GOLD', 'STAR', 'KING', 'MATH', 'ROSE', 'WIND', 'FIRE', 'BLUE', 'MINT', 'NOTE', 'DUSK', 'GLOW', 'IRON', 'JADE', 'OPAL', 'PIKE', 'SNOW', 'TIDE', 'WARP', 'YAWN', 'ZINC', 'CALM', 'DOVE', 'EPIC', 'FOLK', 'GUST', 'KNOT'];
  const good = WORDS.filter((w) => V.hillCheck(w).ok), bad = WORDS.filter((w) => !V.hillCheck(w).ok);
  const chip = (w) => `<button type="button" data-key="${w}" aria-label="${w}, determinant ${V.hillCheck(w).det}">${w}</button>`;
  $('word-keys').innerHTML = good.map(chip).join('');
  $('bad-keys').innerHTML = bad.slice(0, 12).map(chip).join('');
  $('word-keys').addEventListener('click', (e) => { const w = e.target.dataset && e.target.dataset.key; if (w) useHill(w); });
  $('bad-keys').addEventListener('click', (e) => { const w = e.target.dataset && e.target.dataset.key; if (w) { $('check-key').value = w; keyReport(); } });

  function useHill(w) {
    $('hillkey').value = w;
    hillStatus();
    showTab('encrypt');
    $('hillkey').focus();
  }

  function keyReport() {
    const c = V.hillCheck($('check-key').value), out = $('key-report');
    if (c.normalized.length !== 4) {
      out.innerHTML = `<p class="key-verdict verdict bad">Needs exactly 4 letters.</p><p>It has ${c.normalized.length}. The four letters fill the matrix row by row.</p>`;
      $('use-checked').disabled = true;
      return;
    }
    const v = [...c.normalized].map(num);
    const raw = v[0] * v[3] - v[1] * v[2];
    const mathsCommon = `
      <div class="key-maths">
        <div><span class="label">Matrix H</span>${matrixHtml(c.matrix, 'big')}</div>
        <div><span class="label">Determinant</span>${v[0]}×${v[3]} − ${v[1]}×${v[2]} = ${raw}<br>${raw} mod 26 = <strong>${c.det}</strong></div>
        ${c.ok ? `<div><span class="label">Inverse H⁻¹</span>${matrixHtml(c.inverse, 'big hl')}</div>` : ''}
      </div>`;
    if (c.ok) {
      out.innerHTML = `<p class="key-verdict verdict good">${c.normalized} works.</p><p>The determinant ${c.det} is odd and not 13, so it has an inverse mod 26: ${c.det} × ${c.detInverse} = ${c.det * c.detInverse} ≡ 1. That makes H⁻¹ = ${c.detInverse} × [[${v[3]}, −${v[1]}], [−${v[2]}, ${v[0]}]] mod 26.</p>${mathsCommon}`;
    } else {
      out.innerHTML = `<p class="key-verdict verdict bad">${c.normalized} doesn't work.</p><p>${esc(c.reason)}</p>${mathsCommon}`;
    }
    $('use-checked').disabled = !c.ok;
  }
  $('check-key').addEventListener('input', keyReport);
  $('gen-key').addEventListener('click', () => { $('check-key').value = V.randomHillKey(); keyReport(); });
  $('use-checked').addEventListener('click', () => { const c = V.hillCheck($('check-key').value); if (c.ok) useHill(c.normalized); });

  keywordStatus();
  hillStatus();
  syncMode();
  keyReport();
  showTab(location.hash.slice(1) || 'encrypt');
})();
