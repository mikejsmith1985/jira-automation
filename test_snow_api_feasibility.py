"""
ServiceNow REST API Feasibility Test
=====================================
Tests whether we can replace Playwright DOM scraping with direct REST API calls
using the existing browser session (no API key needed).

HOW IT WORKS (same trick as the Jira migration tool):
  - Playwright controls a real browser
  - When you're logged into ServiceNow in that browser, session cookies are live
  - page.evaluate() runs JavaScript IN the browser, so fetch() calls to ServiceNow
    automatically include those cookies → authenticated without an API key

WHAT THIS TESTS:
  1. Table API read  (GET  /api/now/table/problem)       - fetch PRB data
  2. CSRF token      (window.g_ck)                       - needed for writes
  3. Table API write (PATCH /api/now/table/problem/{id}) - update PRB fields
  4. Related records (GET  /api/now/table/task_rel_task) - linked incidents

USAGE:
  python test_snow_api_feasibility.py

  You'll be prompted for your ServiceNow URL and a PRB number.
  The browser will open - if you need to log in, do so.
  The test will run automatically once you're authenticated.
"""

import asyncio
import json
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

def get_config():
    """Interactive config — reads from config.yaml if possible, otherwise prompts."""
    snow_url = ''
    prb_number = ''

    # Try to read from config.yaml
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            snow_url = cfg.get('servicenow', {}).get('url', '').strip().rstrip('/')
            if snow_url:
                log.info(f"  ✅ ServiceNow URL loaded from config.yaml: {snow_url}")
        except Exception as e:
            log.warning(f"  ⚠️  Could not read config.yaml: {e}")

    if not snow_url:
        snow_url = input("\n  Enter your ServiceNow URL (e.g. https://yourco.service-now.com): ").strip().rstrip('/')

    prb_number = input("  Enter a PRB number to test with (e.g. PRB0001234): ").strip()
    if not prb_number.upper().startswith('PRB'):
        prb_number = 'PRB' + prb_number

    return snow_url, prb_number.upper()


# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────

RESULTS = []

def record(test_name, passed, detail='', data=None):
    icon = '✅' if passed else '❌'
    RESULTS.append({'test': test_name, 'passed': passed, 'detail': detail, 'data': data})
    log.info(f"  {icon} {test_name}: {detail}")


async def run_tests(snow_url: str, prb_number: str):
    async with async_playwright() as pw:
        log.info("\n  🌐 Launching browser (headed so you can log in if needed)...")
        browser = await pw.chromium.launch(headless=False, args=['--start-maximized'])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        # ── Step 1: Navigate to SNOW and wait for login ────────────────────
        log.info(f"\n  [1/5] Navigating to ServiceNow: {snow_url}")
        log.info("        Log in if prompted, then press Enter here to continue...")
        await page.goto(snow_url, wait_until='domcontentloaded', timeout=60000)

        input("        (Press Enter once you are logged into ServiceNow) ")

        current_url = page.url
        log.info(f"        Current URL: {current_url}")

        # ── Step 2: Test REST API read — get PRB by number ─────────────────
        log.info(f"\n  [2/5] Testing Table API: GET PRB {prb_number}...")

        api_result = await page.evaluate(f"""
            async () => {{
                try {{
                    const resp = await fetch(
                        '/api/now/table/problem?sysparm_query=number={prb_number}&sysparm_limit=1&sysparm_fields=number,short_description,description,state,priority,sys_id,assigned_to,category,problem_category',
                        {{
                            headers: {{
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            }},
                            credentials: 'include'
                        }}
                    );
                    return {{
                        status: resp.status,
                        ok: resp.ok,
                        body: resp.ok ? await resp.json() : await resp.text()
                    }};
                }} catch(e) {{
                    return {{ error: e.toString() }};
                }}
            }}
        """)

        if api_result.get('error'):
            record('Table API (GET)', False, f"Fetch error: {api_result['error']}")
        elif api_result.get('status') == 200:
            records = api_result['body'].get('result', [])
            if records:
                prb = records[0]
                record('Table API (GET)', True,
                       f"HTTP 200 — got PRB: '{prb.get('short_description', '')[:60]}'",
                       data=prb)
                log.info(f"        PRB sys_id: {prb.get('sys_id')}")
                log.info(f"        State:      {prb.get('state')}")
                log.info(f"        Priority:   {prb.get('priority')}")
            else:
                record('Table API (GET)', False, f"HTTP 200 but no records returned for {prb_number}")
        elif api_result.get('status') == 401:
            record('Table API (GET)', False, "HTTP 401 — session not authenticated or API not accessible")
        elif api_result.get('status') == 403:
            record('Table API (GET)', False, "HTTP 403 — authenticated but no API read permission for 'problem' table")
        else:
            record('Table API (GET)', False, f"HTTP {api_result.get('status')}: {str(api_result.get('body', ''))[:200]}")

        # ── Step 3: Get CSRF token (needed for writes) ─────────────────────
        log.info(f"\n  [3/5] Testing CSRF token availability (window.g_ck)...")

        csrf_result = await page.evaluate("""
            () => {
                // ServiceNow stores CSRF token in window.g_ck
                // Also try alternate locations
                return {
                    g_ck: typeof window.g_ck !== 'undefined' ? window.g_ck : null,
                    has_g_ck: typeof window.g_ck !== 'undefined',
                    meta_token: document.querySelector('meta[name="csrf-token"]')?.content || null,
                    g_form_available: typeof window.g_form !== 'undefined'
                };
            }
        """)

        if csrf_result.get('has_g_ck') and csrf_result['g_ck']:
            record('CSRF Token (g_ck)', True, f"Available: {csrf_result['g_ck'][:12]}…", data=csrf_result)
        elif csrf_result.get('meta_token'):
            record('CSRF Token (meta)', True, f"Via meta tag: {csrf_result['meta_token'][:12]}…", data=csrf_result)
        else:
            record('CSRF Token', False,
                   "Not found on current page — navigate to a SNOW page with a form to get g_ck",
                   data=csrf_result)
            # Navigate to a real SNOW page to get the token
            log.info("        Navigating to a SNOW form page to find g_ck...")
            await page.goto(f"{snow_url}/nav_to.do?uri=problem_list.do", wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            csrf_retry = await page.evaluate("() => ({ g_ck: typeof window.g_ck !== 'undefined' ? window.g_ck : null })")
            if csrf_retry.get('g_ck'):
                record('CSRF Token (after nav)', True, f"Found after navigating to SNOW page: {csrf_retry['g_ck'][:12]}…")

        # ── Step 4: Test write (PATCH) using session + CSRF token ──────────
        log.info(f"\n  [4/5] Testing Table API write (PATCH — dry run, no real change)...")

        # Only try if we have a sys_id from the read test
        prb_sys_id = None
        for r in RESULTS:
            if r['test'] == 'Table API (GET)' and r['passed'] and r.get('data'):
                prb_sys_id = r['data'].get('sys_id')

        if not prb_sys_id:
            record('Table API (PATCH)', False, "Skipped — no sys_id available (read test failed)")
        else:
            # Get the current CSRF token from any available source
            csrf_token = await page.evaluate("""
                () => window.g_ck || document.querySelector('meta[name="csrf-token"]')?.content || ''
            """)

            patch_result = await page.evaluate(f"""
                async () => {{
                    // Dry-run: we fetch with PATCH but send the EXACT same value back
                    // so no actual change is made — just testing auth works
                    try {{
                        // First get current value
                        const getResp = await fetch(
                            '/api/now/table/problem/{prb_sys_id}?sysparm_fields=work_notes',
                            {{ headers: {{'Accept': 'application/json'}}, credentials: 'include' }}
                        );
                        if (!getResp.ok) return {{ status: getResp.status, skipped: true, reason: 'Could not get current value' }};

                        const current = await getResp.json();

                        // PATCH with same value → no visible change, just tests write permission
                        const patchResp = await fetch(
                            '/api/now/table/problem/{prb_sys_id}',
                            {{
                                method: 'PATCH',
                                headers: {{
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json',
                                    'X-UserToken': '{csrf_token}'
                                }},
                                credentials: 'include',
                                body: JSON.stringify({{ work_notes: current?.result?.work_notes || '' }})
                            }}
                        );
                        return {{
                            status: patchResp.status,
                            ok: patchResp.ok,
                            body: patchResp.ok ? 'success' : await patchResp.text()
                        }};
                    }} catch(e) {{
                        return {{ error: e.toString() }};
                    }}
                }}
            """)

            if patch_result.get('error'):
                record('Table API (PATCH)', False, f"Fetch error: {patch_result['error']}")
            elif patch_result.get('status') == 200:
                record('Table API (PATCH)', True, "HTTP 200 — write access confirmed (dry run, no change made)")
            elif patch_result.get('status') == 403:
                record('Table API (PATCH)', False, "HTTP 403 — read works but no write permission on 'problem' table")
            elif patch_result.get('status') == 401:
                record('Table API (PATCH)', False, "HTTP 401 — session expired or CSRF token invalid")
            else:
                record('Table API (PATCH)', False,
                       f"HTTP {patch_result.get('status')}: {str(patch_result.get('body',''))[:200]}")

        # ── Step 5: Test related incidents query ───────────────────────────
        log.info(f"\n  [5/5] Testing related incidents (task_rel_task)...")

        if not prb_sys_id:
            record('Related Records (GET)', False, "Skipped — no sys_id available")
        else:
            rel_result = await page.evaluate(f"""
                async () => {{
                    try {{
                        const resp = await fetch(
                            '/api/now/table/task_rel_task?sysparm_query=parent={prb_sys_id}&sysparm_fields=child.number,child.short_description,child.sys_class_name&sysparm_limit=20',
                            {{
                                headers: {{'Accept': 'application/json'}},
                                credentials: 'include'
                            }}
                        );
                        return {{
                            status: resp.status,
                            ok: resp.ok,
                            body: resp.ok ? await resp.json() : await resp.text()
                        }};
                    }} catch(e) {{
                        return {{ error: e.toString() }};
                    }}
                }}
            """)

            if rel_result.get('status') == 200:
                records = rel_result['body'].get('result', [])
                record('Related Records (GET)', True,
                       f"HTTP 200 — found {len(records)} related record(s)")
                for rec in records[:5]:
                    child = rec.get('child.number', rec.get('child', {}).get('number', 'unknown'))
                    log.info(f"        → {child}")
            else:
                record('Related Records (GET)', False,
                       f"HTTP {rel_result.get('status', 'ERR')}: {str(rel_result.get('body', ''))[:200]}")

        # ── Save results ───────────────────────────────────────────────────
        await _save_report(snow_url, prb_number)
        await browser.close()


async def _save_report(snow_url, prb_number):
    """Save a JSON + human-readable report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join(os.path.dirname(__file__), 'diagnostics')
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, f'snow_api_feasibility_{timestamp}.json')

    report = {
        'timestamp': timestamp,
        'snow_url': snow_url,
        'prb_number': prb_number,
        'results': RESULTS,
        'summary': {
            'passed': sum(1 for r in RESULTS if r['passed']),
            'failed': sum(1 for r in RESULTS if not r['passed']),
            'total': len(RESULTS)
        }
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    _print_summary(report, report_path)


def _print_summary(report, report_path):
    passed = report['summary']['passed']
    total  = report['summary']['total']
    failed = report['summary']['failed']

    log.info("\n")
    log.info("  ══════════════════════════════════════════════════════")
    log.info("   SERVICENOW REST API FEASIBILITY RESULTS")
    log.info("  ══════════════════════════════════════════════════════")

    for r in RESULTS:
        icon = '✅' if r['passed'] else '❌'
        log.info(f"   {icon}  {r['test']}")
        log.info(f"        {r['detail']}")

    log.info("")
    log.info(f"   Result: {passed}/{total} tests passed")
    log.info("")

    if passed == total:
        log.info("  🎉 FULL REST API ACCESS CONFIRMED")
        log.info("     The browser session approach works perfectly.")
        log.info("     We can replace ALL Playwright DOM scraping with clean")
        log.info("     REST API calls — no API key needed, no fragile selectors.")
        log.info("")
        log.info("  NEXT STEP: Replace servicenow_scraper.py with a REST client")
        log.info("  that calls page.evaluate(fetch('/api/now/table/...')) instead")
        log.info("  of navigating to PRB pages and scraping the DOM.")

    elif passed >= 3:
        log.info("  ✅ READ ACCESS CONFIRMED (write may need permissions fix)")
        log.info("     We can at minimum replace the DOM scraping for data extraction.")
        if failed:
            log.info("     Failed tests suggest some ServiceNow role/permission gaps.")
            log.info("     Ask your SNOW admin for 'rest_api_explorer' or 'itil' role.")

    elif passed >= 1:
        log.info("  ⚠️  PARTIAL ACCESS — session auth works but permissions limited")
        log.info("     Check the failed tests above. SNOW admin may need to grant")
        log.info("     REST API access to your user role.")

    else:
        log.info("  ❌ REST API NOT ACCESSIBLE VIA BROWSER SESSION")
        log.info("     This instance likely has the REST API locked down")
        log.info("     or requires a separate API-specific credential.")
        log.info("     You would need a ServiceNow API key / OAuth token.")
        log.info("")
        log.info("     Alternative: Ask SNOW admin for a service account with")
        log.info("     REST API access — only basic 'problem' table read is needed.")

    log.info("")
    log.info(f"  📄 Full report saved: {report_path}")
    log.info("  ══════════════════════════════════════════════════════")
    log.info("")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║  ServiceNow REST API Feasibility Test             ║")
    print("  ║  (Uses your browser session — no API key needed)  ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print()
    print("  This test checks if we can access ServiceNow's REST API")
    print("  using your existing browser login session — the same approach")
    print("  that worked for Jira. If it works, we can replace all the")
    print("  fragile DOM scraping with clean, reliable API calls.")
    print()

    snow_url, prb_number = get_config()

    print()
    print(f"  Testing: {snow_url}")
    print(f"  PRB:     {prb_number}")
    print()

    asyncio.run(run_tests(snow_url, prb_number))
