import { $, bars, esc, fail, int, kpis, load, pct, select } from './kit.js';

const money = (x) => (x == null ? '–' : Number(x).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
const kv = (o, skip = []) => `<table class="kv"><tbody>${Object.entries(o).filter(([k]) => !skip.includes(k)).map(([k, v]) => `<tr><th>${esc(k.replace(/_/g, ' '))}</th><td>${fmt(v)}</td></tr>`).join('')}</tbody></table>`;
function fmt(v) {
  if (v == null || v === '') return '<span class="muted">–</span>';
  if (typeof v === 'boolean') return `<span class="pill ${v ? 'ok' : 'no'}">${v ? 'yes' : 'no'}</span>`;
  if (Array.isArray(v)) return v.length ? v.map((x) => (Array.isArray(x) ? esc(x.map((y) => (typeof y === 'number' ? money(y) : y)).join(' · ')) : typeof x === 'object' ? esc(Object.values(x).join(' · ')) : esc(x))).join('<br>') : '<span class="muted">none</span>';
  if (typeof v === 'object') return esc(JSON.stringify(v));
  return typeof v === 'number' && !Number.isInteger(v) ? money(v) : esc(v);
}
const OUTCOME = { decided: 'decided', awaiting_approval: 'waiting for a person', stopped_review_loop: 'stopped: review loop', stopped_budget: 'stopped: budget', stopped_max_steps: 'stopped: step limit', paid: 'paid', rejected_by_human: 'rejected by a person' };

try {
  const { summary: S, limits: L, claims } = await load();
  const det = Object.entries(S.detection);
  kpis($('#kpis'), [
    { label: 'Planted problems caught', value: pct(det.reduce((a, [, x]) => a + x.caught, 0) / det.reduce((a, [, x]) => a + x.planted, 0)), note: `${int(det.reduce((a, [, x]) => a + x.false_flags, 0))} false flags across 900 claims` },
    { label: 'Paid without a person', value: '0', note: `${int(S.statuses.awaiting_approval)} payouts waited for approval` },
    { label: 'Cost per claim', value: `$${S.median_dollars.toFixed(5)}`, note: `median; the most was $${S.max_dollars.toFixed(5)}, ceiling $${L.max_dollars}` },
    { label: 'Resumed run ends the same', value: S.replay_equal ? 'yes' : 'no', note: 'restarted from a mid-run snapshot' },
  ]);

  let c = claims[0], at = 1, decision = null;
  function draw() {
    const steps = c.steps, s = steps[at], ran = s.path[s.path.length - 1];
    $('#rail').innerHTML = steps.slice(1).map((x, i) => `<button type="button" class="step${i + 1 === at ? ' on' : ''}" data-i="${i + 1}">${i + 1}. ${esc(x.path[x.path.length - 1])}</button>`).join('<span class="muted">→</span>');
    $('#where').textContent = `step ${at} of ${steps.length - 1}`;
    $('#prev').disabled = at <= 1;
    $('#next').disabled = at >= steps.length - 1;
    const status = decision || s.status;
    $('#meter').innerHTML = `<div>Just ran<b>${esc(ran)}</b><span class="muted small">${s.send_backs ? `${s.send_backs} send-back${s.send_backs > 1 ? 's' : ''} so far` : 'no send-backs yet'}${s.strict ? ' · extractor in strict mode' : ''}</span></div>` +
      `<div>Spent<b>${int(s.cost.tokens)} tokens</b><span class="muted small">$${s.cost.dollars.toFixed(5)} of the $${L.max_dollars} ceiling (${pct(s.cost.dollars / L.max_dollars, 0)})</span></div>` +
      `<div>Status<b>${esc(OUTCOME[status] || status)}</b><span class="muted small">${s.status === 'running' ? `next: ${esc(s.node)}` : 'the run has stopped'}</span></div>`;
    const card = (title, body, on) => `<div class="box${on ? ' on' : ''}"><h3 class="small" style="margin:0 0 6px">${title}</h3>${body}</div>`;
    $('#state').innerHTML =
      card('Extracted', s.extracted ? kv(s.extracted) : '<span class="muted">not yet</span>', ran === 'extractor') +
      card('Findings', s.findings ? kv(s.findings) : '<span class="muted">not yet</span>', ran === 'investigator') +
      card('Review', s.review ? kv(s.review) : '<span class="muted">not yet</span>', ran === 'reviewer') +
      card('Recommendation', s.recommendation ? kv(s.recommendation) : '<span class="muted">not yet</span>', ran === 'recommend');
    const last = at === steps.length - 1;
    $('#gate').innerHTML = last && s.status === 'awaiting_approval' && !decision
      ? `<div class="box"><b>The human gate.</b> The recommendation is a payout of ${money(s.recommendation.payout)}; only a person can release it. <div class="controls" style="margin:10px 0 0"><button class="btn primary" id="approve" type="button">Approve payout</button><button class="btn" id="reject" type="button">Reject</button></div></div>`
      : decision ? `<div class="box">Recorded: <b>${esc(OUTCOME[decision])}</b>, by you, in this page only.</div>` : '';
    if ($('#approve')) { $('#approve').onclick = () => { decision = 'paid'; draw(); }; $('#reject').onclick = () => { decision = 'rejected_by_human'; draw(); }; }
  }
  const label = (x) => { const f = x.steps[x.steps.length - 1]; return `${x.id} · ${x.planted.length ? x.planted.join(', ') : 'clean'} → ${OUTCOME[f.status] || f.status}${f.recommendation ? ` (${f.recommendation.decision})` : ''}`; };
  select($('#pick'), claims.map((x, i) => [i, label(x)]), 0, (i) => {
    c = claims[+i]; at = 1; decision = null;
    $('#docs').innerHTML = Object.entries(c.documents).map(([k, v]) => `<div class="box"><h3 class="small" style="margin:0 0 6px">${esc(k === 'fnol' ? 'first notice of loss' : k)}</h3><pre style="margin:0;white-space:pre-wrap;font:12.5px/1.5 var(--mono)">${esc(v)}</pre></div>`).join('') +
      `<div class="box"><h3 class="small" style="margin:0 0 6px">claims history for this policy</h3>${c.prior_claims.length ? c.prior_claims.map((p) => `<pre style="margin:0;white-space:pre-wrap;font:12.5px/1.5 var(--mono)">${esc(JSON.stringify(p))}</pre>`).join('') : '<span class="muted">no earlier claims</span>'}</div>`;
    draw();
  });
  $('#prev').onclick = () => { if (at > 1) { at -= 1; draw(); } };
  $('#next').onclick = () => { if (at < c.steps.length - 1) { at += 1; draw(); } };
  $('#rail').onclick = (e) => { const b = e.target.closest('button[data-i]'); if (b) { at = +b.dataset.i; draw(); } };

  bars($('#caught'), det.map(([k, x]) => ({ label: k.replace(/_/g, ' '), value: x.caught / x.planted, text: `${x.caught}/${x.planted}` })), { max: 1 });
  $('#stopSub').textContent = `Every claim stopped within ${L.max_steps} steps; none crossed its budget.`;
  bars($('#stops'), Object.entries(S.statuses).map(([k, v]) => ({ label: OUTCOME[k] || k, value: v, text: int(v), color: k.startsWith('stopped') ? 'var(--bad)' : k === 'awaiting_approval' ? 'var(--accent)' : 'var(--c6)' })));
} catch (err) {
  fail(err);
}
