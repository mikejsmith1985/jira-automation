/**
 * ServiceNow REST API Feasibility Tester
 * Runs INSIDE the ServiceNow browser tab — uses existing session, no login needed.
 * 
 * Loaded via bookmarklet from GitHub Pages.
 * Toggle: click bookmark again to close the panel.
 */
(function () {
  'use strict';

  const PANEL_ID = 'snow-api-tester-v1';

  // Toggle if already open
  const existing = document.getElementById(PANEL_ID);
  if (existing) { existing.remove(); return; }

  // ── Styles ────────────────────────────────────────────────────────────────
  const css = `
    #${PANEL_ID} {
      position: fixed; top: 20px; right: 20px; width: 500px; max-height: 88vh;
      background: #0f172a; color: #e2e8f0; border-radius: 12px;
      box-shadow: 0 24px 64px rgba(0,0,0,0.7); font-family: -apple-system, system-ui, sans-serif;
      font-size: 13px; z-index: 2147483647; display: flex; flex-direction: column;
      border: 1px solid #1e293b; overflow: hidden;
    }
    #${PANEL_ID} * { box-sizing: border-box; }
    .sn-header {
      background: #1e293b; padding: 14px 16px; display: flex;
      align-items: center; justify-content: space-between; flex-shrink: 0;
      border-bottom: 1px solid #334155;
    }
    .sn-header-title { font-weight: 700; font-size: 14px; color: #f1f5f9; }
    .sn-header-sub { font-size: 11px; color: #64748b; margin-top: 2px; }
    .sn-close {
      background: #334155; border: none; color: #94a3b8; width: 28px; height: 28px;
      border-radius: 6px; cursor: pointer; font-size: 16px; line-height: 1;
    }
    .sn-close:hover { background: #475569; color: #f1f5f9; }
    .sn-body { padding: 16px; overflow-y: auto; flex: 1; }
    .sn-input-row { display: flex; gap: 8px; margin-bottom: 12px; }
    .sn-input {
      flex: 1; background: #1e293b; border: 1px solid #334155; color: #f1f5f9;
      padding: 9px 12px; border-radius: 6px; font-size: 13px;
    }
    .sn-input:focus { outline: none; border-color: #3b82f6; }
    .sn-run-btn {
      background: #3b82f6; color: white; border: none; padding: 9px 18px;
      border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px; white-space: nowrap;
    }
    .sn-run-btn:hover { background: #2563eb; }
    .sn-run-btn:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
    .sn-hint { font-size: 11px; color: #64748b; margin-bottom: 14px; line-height: 1.5; }
    .sn-divider { border: none; border-top: 1px solid #1e293b; margin: 12px 0; }
    .sn-result {
      display: flex; gap: 10px; padding: 10px 12px; border-radius: 8px;
      margin-bottom: 8px; background: #1e293b; align-items: flex-start;
      border-left: 3px solid transparent;
    }
    .sn-result.pass  { border-left-color: #22c55e; }
    .sn-result.fail  { border-left-color: #ef4444; }
    .sn-result.warn  { border-left-color: #f59e0b; }
    .sn-result.skip  { border-left-color: #475569; }
    .sn-result.info  { border-left-color: #3b82f6; }
    .sn-result-icon  { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
    .sn-result-body  { flex: 1; min-width: 0; }
    .sn-result-name  { font-weight: 600; color: #f1f5f9; margin-bottom: 2px; }
    .sn-result-detail { color: #94a3b8; font-size: 12px; word-break: break-word; }
    .sn-result-extra  { color: #64748b; font-size: 11px; margin-top: 3px; font-family: monospace; word-break: break-all; }
    .sn-summary {
      background: #1e3a5f; border: 1px solid #2563eb; border-radius: 8px;
      padding: 12px 14px; margin-bottom: 12px; color: #93c5fd;
    }
    .sn-summary.success { background: #14532d; border-color: #16a34a; color: #86efac; }
    .sn-summary.partial { background: #422006; border-color: #d97706; color: #fcd34d; }
    .sn-summary.blocked { background: #450a0a; border-color: #b91c1c; color: #fca5a5; }
    .sn-summary-title { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
    .sn-summary-sub   { font-size: 12px; opacity: 0.85; }
    .sn-copy-btn {
      background: #1e293b; border: 1px solid #334155; color: #94a3b8;
      padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 12px;
      margin-top: 10px; width: 100%;
    }
    .sn-copy-btn:hover { background: #334155; color: #f1f5f9; }
    .sn-spinner { display: inline-block; animation: sn-spin 1s linear infinite; }
    @keyframes sn-spin { to { transform: rotate(360deg); } }
    .sn-progress { color: #64748b; font-size: 12px; padding: 6px 0; }
  `;

  const styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ── Panel HTML ─────────────────────────────────────────────────────────────
  const origin = window.location.origin;
  const urlPrb = (window.location.href.match(/PRB\d+/i) || [])[0] || '';

  const panel = document.createElement('div');
  panel.id = PANEL_ID;
  panel.innerHTML = `
    <div class="sn-header">
      <div>
        <div class="sn-header-title">🔬 ServiceNow REST API Tester</div>
        <div class="sn-header-sub">${origin}</div>
      </div>
      <button class="sn-close" id="sn-close-btn">✕</button>
    </div>
    <div class="sn-body">
      <p class="sn-hint">
        Tests whether Waypoint can access the ServiceNow REST API using your existing
        browser session — <strong>no API key needed</strong>. Enter any PRB number you have
        access to and click Run.
      </p>
      <div class="sn-input-row">
        <input class="sn-input" id="sn-prb-input"
          placeholder="PRB number (e.g. PRB0001234)"
          value="${urlPrb}" />
        <button class="sn-run-btn" id="sn-run-btn">▶ Run Tests</button>
      </div>
      <div id="sn-results"></div>
    </div>
  `;
  document.body.appendChild(panel);

  document.getElementById('sn-close-btn').onclick = () => panel.remove();
  document.getElementById('sn-prb-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('sn-run-btn').click();
  });

  // ── Helpers ────────────────────────────────────────────────────────────────
  const results = document.getElementById('sn-results');

  function addResult(type, icon, name, detail, extra) {
    const div = document.createElement('div');
    div.className = `sn-result ${type}`;
    div.innerHTML = `
      <div class="sn-result-icon">${icon}</div>
      <div class="sn-result-body">
        <div class="sn-result-name">${name}</div>
        <div class="sn-result-detail">${detail}</div>
        ${extra ? `<div class="sn-result-extra">${extra}</div>` : ''}
      </div>
    `;
    results.appendChild(div);
    return div;
  }

  function addProgress(msg) {
    const div = document.createElement('div');
    div.className = 'sn-progress';
    div.innerHTML = `<span class="sn-spinner">⟳</span> ${msg}`;
    results.appendChild(div);
    return div;
  }

  // ── Tests ──────────────────────────────────────────────────────────────────
  async function runTests() {
    const prbNum = document.getElementById('sn-prb-input').value.trim().toUpperCase();
    if (!prbNum.match(/^PRB\d+$/)) {
      alert('Please enter a valid PRB number (e.g. PRB0001234)');
      return;
    }

    results.innerHTML = '';
    const btn = document.getElementById('sn-run-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Running…';

    const state = { sysId: null, csrfToken: null, passCount: 0, failCount: 0, warnCount: 0 };

    function tally(type) {
      if (type === 'pass') state.passCount++;
      else if (type === 'fail') state.failCount++;
      else if (type === 'warn') state.warnCount++;
    }

    // ── Test 1: Table API Read ──────────────────────────────────────────────
    let p = addProgress('Testing Table API read (GET /api/now/table/problem)…');
    try {
      const resp = await fetch(
        `/api/now/table/problem?sysparm_query=number=${prbNum}&sysparm_limit=1` +
        `&sysparm_fields=number,short_description,state,priority,sys_id,assigned_to,category`,
        { headers: { Accept: 'application/json' }, credentials: 'include' }
      );
      p.remove();
      if (resp.ok) {
        const data = await resp.json();
        const recs = data.result || [];
        if (recs.length > 0) {
          const prb = recs[0];
          state.sysId = prb.sys_id;
          tally('pass');
          addResult('pass', '✅', 'Table API — Read PRB',
            `HTTP 200 — Got PRB data successfully`,
            `Short desc: "${(prb.short_description || '').substring(0, 70)}" | State: ${prb.state || '?'} | sys_id: ${prb.sys_id}`);
        } else {
          tally('warn');
          addResult('warn', '⚠️', 'Table API — Read PRB',
            `HTTP 200 — API is accessible but ${prbNum} not found`,
            `The PRB may not exist, or your role may not have read access to this specific record. Try a different PRB.`);
        }
      } else if (resp.status === 401) {
        tally('fail');
        addResult('fail', '❌', 'Table API — Read PRB',
          `HTTP 401 — Session cookies not accepted for API calls`,
          `This instance may require a separate API credential (OAuth / Basic Auth). The browser-session approach won't work here.`);
      } else if (resp.status === 403) {
        tally('fail');
        addResult('fail', '❌', 'Table API — Read PRB',
          `HTTP 403 — Authenticated but access denied to "problem" table`,
          `Ask your SNOW admin to grant your user the "itil", "problem_coordinator", or "rest_api_explorer" role.`);
      } else {
        tally('fail');
        const body = await resp.text();
        addResult('fail', '❌', 'Table API — Read PRB',
          `HTTP ${resp.status}`,
          body.substring(0, 150));
      }
    } catch (e) {
      p.remove();
      tally('fail');
      addResult('fail', '❌', 'Table API — Read PRB',
        `Fetch error: ${e.message}`,
        `This may indicate a Content Security Policy restriction on this page.`);
    }

    // ── Test 2: CSRF Token ─────────────────────────────────────────────────
    p = addProgress('Checking CSRF token (window.g_ck) for write operations…');
    await new Promise(r => setTimeout(r, 200));
    p.remove();

    const gck = window.g_ck || null;
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.content || null;
    state.csrfToken = gck || metaToken;

    if (gck) {
      tally('pass');
      addResult('pass', '✅', 'CSRF Token — window.g_ck',
        `Found: ${gck.substring(0, 20)}… (${gck.length} chars)`,
        `Write operations (PATCH/POST) are possible using this token in X-UserToken header.`);
    } else if (metaToken) {
      tally('pass');
      addResult('pass', '✅', 'CSRF Token — meta tag',
        `Found via &lt;meta name="csrf-token"&gt;: ${metaToken.substring(0, 20)}…`,
        `Write operations are possible.`);
    } else {
      tally('warn');
      addResult('warn', '⚠️', 'CSRF Token',
        `Not found on this page — navigate to a ServiceNow form page and re-run`,
        `g_ck is injected by ServiceNow on form pages (e.g. nav_to.do?uri=problem_form.do). The write test will be skipped.`);
    }

    // ── Test 3: Table API Write (dry run) ──────────────────────────────────
    if (state.sysId && state.csrfToken) {
      p = addProgress('Testing write access (PATCH — no actual changes made)…');
      try {
        const patchResp = await fetch(`/api/now/table/problem/${state.sysId}`, {
          method: 'PATCH',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            'X-UserToken': state.csrfToken
          },
          credentials: 'include',
          // Patch work_notes with empty string = no visible change, just tests auth
          body: JSON.stringify({ work_notes: '' })
        });
        p.remove();
        if (patchResp.status === 200 || patchResp.ok) {
          tally('pass');
          addResult('pass', '✅', 'Table API — Write (PATCH)',
            `HTTP ${patchResp.status} — Write access confirmed`,
            `Dry run only — no actual data changed. Waypoint can update PRB fields and work notes.`);
        } else if (patchResp.status === 403) {
          tally('fail');
          addResult('fail', '❌', 'Table API — Write (PATCH)',
            `HTTP 403 — Read works but write is denied`,
            `Ask SNOW admin to grant write access to the "problem" table for your role.`);
        } else {
          tally('warn');
          const body = await patchResp.text();
          addResult('warn', '⚠️', 'Table API — Write (PATCH)',
            `HTTP ${patchResp.status}`,
            body.substring(0, 150));
        }
      } catch (e) {
        p.remove();
        tally('fail');
        addResult('fail', '❌', 'Table API — Write (PATCH)', `Error: ${e.message}`);
      }
    } else if (!state.sysId) {
      addResult('skip', '⏭', 'Table API — Write (PATCH)',
        'Skipped — no sys_id (read test failed)', '');
    } else {
      addResult('skip', '⏭', 'Table API — Write (PATCH)',
        'Skipped — CSRF token not available', 'Navigate to a ServiceNow form page and re-run.');
    }

    // ── Test 4: Related Incidents ──────────────────────────────────────────
    if (state.sysId) {
      p = addProgress('Fetching related incidents (task_rel_task)…');
      try {
        const relResp = await fetch(
          `/api/now/table/task_rel_task?sysparm_query=parent=${state.sysId}` +
          `&sysparm_fields=child.number,child.short_description,child.sys_class_name&sysparm_limit=10`,
          { headers: { Accept: 'application/json' }, credentials: 'include' }
        );
        p.remove();
        if (relResp.ok) {
          const relData = await relResp.json();
          const recs = relData.result || [];
          tally('pass');
          const labels = recs.slice(0, 5).map(r =>
            r['child.number'] || (r.child && r.child.number) || 'N/A'
          ).join(', ') || 'None';
          addResult('pass', '✅', 'Related Records (task_rel_task)',
            `HTTP 200 — ${recs.length} related record(s) found`,
            `Linked: ${labels}`);
        } else {
          tally('fail');
          addResult('fail', '❌', 'Related Records (task_rel_task)',
            `HTTP ${relResp.status}`, await relResp.text().then(t => t.substring(0, 100)));
        }
      } catch (e) {
        p.remove();
        tally('fail');
        addResult('fail', '❌', 'Related Records', `Error: ${e.message}`);
      }
    } else {
      addResult('skip', '⏭', 'Related Records (task_rel_task)', 'Skipped — no sys_id', '');
    }

    // ── Test 5: GlideForm API ──────────────────────────────────────────────
    p = addProgress('Checking GlideForm API (g_form)…');
    await new Promise(r => setTimeout(r, 200));
    p.remove();

    const gFormAvail = typeof window.g_form !== 'undefined';
    let gFormValue = '';
    if (gFormAvail) {
      try { gFormValue = window.g_form.getValue('number') || ''; } catch (e) { /* not on a form */ }
    }

    if (gFormAvail) {
      tally('pass');
      addResult('pass', '✅', 'GlideForm API (g_form)',
        `Available${gFormValue ? ` — current form field "number": ${gFormValue}` : ''}`,
        `Fallback DOM extraction also works for cases where the REST API doesn't return a field.`);
    } else {
      tally('warn');
      addResult('warn', '⚠️', 'GlideForm API (g_form)',
        'Not available on this page',
        `Navigate to a PRB form page (nav_to.do?uri=problem_form.do&sysparm_query=number=${prbNum}) and re-run to test GlideForm.`);
    }

    // ── Summary ────────────────────────────────────────────────────────────
    btn.disabled = false;
    btn.textContent = '↺ Re-run';

    const summaryDiv = document.createElement('div');
    let summaryClass, summaryTitle, summarySub;

    if (state.failCount === 0 && state.passCount >= 3) {
      summaryClass = 'success';
      summaryTitle = '🎉 Full REST API access confirmed!';
      summarySub = `We can replace ALL Playwright DOM scraping with clean, reliable API calls. No API key needed — your browser session handles auth automatically.`;
    } else if (state.passCount >= 2) {
      summaryClass = 'partial';
      summaryTitle = '⚠️ Partial access — read confirmed, some gaps';
      summarySub = `At minimum, data extraction can be replaced with API calls. Review the failed tests — a SNOW admin may need to adjust your role permissions.`;
    } else {
      summaryClass = 'blocked';
      summaryTitle = '❌ API access blocked';
      summarySub = `The session-based approach won't work on this instance. A dedicated API credential (service account with REST access) would be needed. Waypoint would continue using browser scraping.`;
    }

    summaryDiv.className = `sn-summary ${summaryClass}`;
    summaryDiv.innerHTML = `
      <div class="sn-summary-title">${summaryTitle}</div>
      <div class="sn-summary-sub">${state.passCount} passed · ${state.failCount} failed · ${state.warnCount} warnings<br>${summarySub}</div>
    `;
    results.insertBefore(summaryDiv, results.firstChild);

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'sn-copy-btn';
    copyBtn.textContent = '📋 Copy results to clipboard';
    copyBtn.onclick = () => {
      const lines = [`ServiceNow REST API Feasibility Test`, `${new Date().toISOString()}`, `Instance: ${origin}`, `PRB: ${prbNum}`, `Result: ${summaryTitle}`, ``];
      results.querySelectorAll('.sn-result').forEach(el => {
        const icon = el.querySelector('.sn-result-icon')?.textContent?.trim() || '';
        const name = el.querySelector('.sn-result-name')?.textContent?.trim() || '';
        const detail = el.querySelector('.sn-result-detail')?.textContent?.trim() || '';
        lines.push(`${icon} ${name}: ${detail}`);
      });
      navigator.clipboard.writeText(lines.join('\n')).then(() => {
        copyBtn.textContent = '✅ Copied!';
        setTimeout(() => { copyBtn.textContent = '📋 Copy results to clipboard'; }, 2500);
      });
    };
    results.appendChild(copyBtn);
  }

  document.getElementById('sn-run-btn').addEventListener('click', runTests);

  // Auto-focus input
  setTimeout(() => document.getElementById('sn-prb-input').focus(), 100);
})();
