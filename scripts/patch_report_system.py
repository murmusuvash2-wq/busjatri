#!/usr/bin/env python3
"""Report system Phase B — wire submissions + contributors line.

Visitor reports ('time galat', 'bus abhi nahi chalti', 'route badal gaya')
and '+ Add time' entries now go to the BusJatri receiver (Apps Script web
app). Endpoint URL is set in REPORT_FORM.action in js/extras.js once
deployed; until then submissions are silent no-ops.

Edits:
 1. js/extras.js   — new report section (type select + name + new sendReport)
                          + loadContributors() for the footer credit line
 2. js/ux-fixes.js — '+ Add time' mini box: optional name input, and every
                           save also POSTs to the review queue
 3. index.html     — footer <p id="bjContrib"> + cache-bust bumps
 4. css/extras.css — .rf-row select styling
 5. css/ux-fixes.css — .bj-timebox name input width

Idempotent; --write to apply.
"""
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    if not args.write:
        print('dry run - use --write to apply')
        return

    # ---------- 1) js/extras.js : replace report section -----------
    p = 'js/extras.js'
    s = open(p, encoding='utf-8').read()
    if 'bjReportType' not in s:
        A = '/* ---------- Report Time'
        B = '/* ---------- Admin Dashboard (demo actions) ----------'
        i, j = s.index(A), s.index(B)
        new_section = '''/* ---------- Report / Suggest - on bus detail pages ----------
   Submits to the BusJatri receiver (Google Apps Script web app).
   REPORT_FORM.action holds the web-app URL once deployed.
   Types: time-report | bus-stopped | route-change | add-time (from the
   + mini box in ux-fixes.js). No email, no login, no popup. */
var REPORT_FORM = { action: "" };   // <-- Apps Script web-app URL goes here
var REPORT_CTX = null;
/* Silent report submit - no email, no popup. Fire-and-forget. */
function sendReport(payload) {
  var url = window.BJ_REPORT_URL || REPORT_FORM.action;
  if (!url) return false;
  try {
    var body = new URLSearchParams();
    Object.keys(payload).forEach(function (k) { body.append(k, payload[k] == null ? "" : payload[k]); });
    fetch(url, { method: "POST", mode: "no-cors", body: body });
  } catch (e) { /* never bother the user */ }
  return true;
}
function toggleReport(btn) {
  var existing = document.getElementById("bjReportForm");
  if (existing) { existing.remove(); return; }
  REPORT_CTX = {
    id: btn.getAttribute("data-id") || "",
    bus: btn.getAttribute("data-bus") || "",
    reg: btn.getAttribute("data-reg") || "",
    org: btn.getAttribute("data-org") || "",
    dest: btn.getAttribute("data-dest") || "",
    dep: btn.getAttribute("data-dep") || ""
  };
  var f = document.createElement("div");
  f.className = "report-form show";
  f.id = "bjReportForm";
  var bn = document.body.classList.contains("lang-bn");
  var savedName = "";
  try { savedName = localStorage.getItem("bj-name") || ""; } catch (e) {}
  f.innerHTML =
    '<div class="rf-title">' + (bn ? "\\u0995\\u09bf\\u099b\\u09c1 \\u09ad\\u09c1\\u09b2? \\u099c\\u09be\\u09a8\\u09bf\\u09df\\u09c7 \\u09a6\\u09bf\\u09a8:" : "Kuch galat? Bata dein:") + '</div>' +
    '<div class="rf-row">' +
      '<select id="bjReportType" aria-label="Report type">' +
        '<option value="time-report">' + (bn ? "\\u09b8\\u09ae\\u09df \\u09ad\\u09c1\\u09b2" : "Time galat hai") + '</option>' +
        '<option value="bus-stopped">' + (bn ? "\\u09ac\\u09be\\u09b8 \\u098f\\u0996\\u09a8 \\u099a\\u09b2\\u09c7 \\u09a8\\u09be" : "Bus abhi nahi chalti") + '</option>' +
        '<option value="route-change">' + (bn ? "\\u09b0\\u09c1\\u099f \\u09ac\\u09a6\\u09b2\\u09c7 \\u0997\\u09c7\\u099b\\u09c7" : "Route badal gaya") + '</option>' +
      '</select>' +
      '<input type="time" id="bjReportTime" aria-label="Correct time">' +
      '<input type="text" id="bjReportNote" placeholder="Note (optional)" maxlength="140">' +
      '<input type="text" id="bjReportName" placeholder="' + (bn ? "\\u09a8\\u09be\\u09ae (optional)" : "Naam (optional)") + '" maxlength="30" value="' + savedName.replace(/"/g, '"') + '">' +
      '<button class="rf-send" onclick="submitReport()">Send</button>' +
    '</div>' +
    '<div class="rf-done" id="bjReportDone">\\u2713 ' + (bn ? "\\u09a7\\u09a8\\u09cd\\u09af\\u09ac\\u09be\\u09a6! \\u09b0\\u09bf\\u09aa\\u09cb\\u09b0\\u09cd\\u099f \\u09aa\\u09be\\u09a0\\u09be\\u09a8\\u09cb \\u09b9\\u09df\\u09c7\\u099b\\u09c7\\u0964" : "Dhanyavaad! Report team ko mil gaya.") + '</div>';
  var row = btn.closest(".wa-row");
  if (row && row.parentNode) row.parentNode.insertBefore(f, row.nextSibling);
  var t = document.getElementById("bjReportTime"); if (t) t.focus();
}
function submitReport() {
  var c = REPORT_CTX || {};
  var sel = document.getElementById("bjReportType");
  var type = sel ? sel.value : "time-report";
  var timeStr = "";
  var inp = document.getElementById("bjReportTime");
  if (type === "time-report") {
    if (!inp || !inp.value) { alert("Please enter the correct time"); return; }
    var parts = inp.value.split(":"); var h = parseInt(parts[0], 10); var m = parts[1];
    var ap = h >= 12 ? "PM" : "AM"; var h12 = h % 12 || 12;
    timeStr = h12 + ":" + m + " " + ap;
  }
  var note = (document.getElementById("bjReportNote") || {}).value || "";
  var name = (document.getElementById("bjReportName") || {}).value || "";
  try { if (name) localStorage.setItem("bj-name", name); } catch (e) {}
  var payload = {
    type: type, bus: c.bus, reg: c.reg, route: (c.org || "") + " \\u21c4 " + (c.dest || ""),
    current: c.dep, time: timeStr, note: note, page: location.href,
    bus_id: c.id, name: name
  };
  sendReport(payload);
  var done = function () {
    var d = document.getElementById("bjReportDone");
    if (d) d.style.display = "block";
    var r = document.getElementById("bjReportForm");
    if (r) { var rw = r.querySelector(".rf-row"); if (rw) rw.style.display = "none"; }
  };
  done();
}

/* ---------- Footer contributors credit line ---------- */
function loadContributors() {
  var el = document.getElementById("bjContrib");
  if (!el) return;
  fetch("data/contributors.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (list) {
      if (!list || !list.length) return;
      while (el.firstChild) el.removeChild(el.firstChild);
      el.appendChild(document.createTextNode("\\u2764 Times improved by: "));
      list.slice(0, 5).forEach(function (c, i) {
        if (i) el.appendChild(document.createTextNode(", "));
        var b = document.createElement("b");
        b.textContent = c.name;
        el.appendChild(b);
      });
      if (list.length > 5) el.appendChild(document.createTextNode(" +" + (list.length - 5) + " more"));
    })
    .catch(function () { /* silent */ });
}

'''
        s = s[:i] + new_section + s[j:]
        print('extras.js: report section replaced')

    old_dcl = 'document.addEventListener("DOMContentLoaded", function () {\n  if (document.querySelector(".search-field")) detectLocation();\n});'
    if old_dcl in s:
        s = s.replace(old_dcl, 'document.addEventListener("DOMContentLoaded", function () {\n  if (document.querySelector(".search-field")) detectLocation();\n  loadContributors();\n});')
        print('extras.js: loadContributors wired on DOMContentLoaded')
    open(p, 'w', encoding='utf-8').write(s)

    # ---------- 2) js/ux-fixes.js : add-time box sends to queue ----------
    p = 'js/ux-fixes.js'
    s = open(p, encoding='utf-8').read()
    if '.bj-name' not in s:
        old_mer = "      '<button type=\"button\" class=\"bj-mer\" title=\"AM/PM\"></button>' +"
        new_mer = ("      '<button type=\"button\" class=\"bj-mer\" title=\"AM/PM\"></button>' +\n"
                   "      '<input type=\"text\" class=\"bj-name\" placeholder=\"Naam (optional)\" maxlength=\"30\" aria-label=\"name\">' +")
        assert s.count(old_mer) == 1, 'bj-mer anchor not found'
        s = s.replace(old_mer, new_mer)
        print('ux-fixes.js: name input added to time box')

        old_save = ("      times[communityTimeKey(busId, stopIndex, direction)] = v;\n"
                    "      try { localStorage.setItem(COMMUNITY_TIME_KEY, JSON.stringify(times)); } catch (e) {}\n"
                    "      box.remove();\n"
                    "      render();")
        new_save = ("      times[communityTimeKey(busId, stopIndex, direction)] = v;\n"
                    "      try { localStorage.setItem(COMMUNITY_TIME_KEY, JSON.stringify(times)); } catch (e) {}\n"
                    "      /* also send to the review queue - approved ones go live for everyone */\n"
                    "      try {\n"
                    "        var nmI = box.querySelector('.bj-name');\n"
                    "        var nm = nmI ? nmI.value.trim() : '';\n"
                    "        if (nm) { try { localStorage.setItem('bj-name', nm); } catch (e2) {} }\n"
                    "        var bb = (typeof BUSES !== 'undefined' && BUSES[busId]) || null;\n"
                    "        var stn = (bb && bb.stoppages && bb.stoppages[stopIndex]) ? bb.stoppages[stopIndex].name : '';\n"
                    "        if (typeof sendReport === 'function') {\n"
                    "          sendReport({ type: 'add-time', bus: bb ? bb.bus_name : '', bus_id: busId,\n"
                    "            stop: stn || '', dir: direction, time: v, note: '',\n"
                    "            page: location.href, name: nm, reg: bb ? (bb.reg_no || '') : '',\n"
                    "            route: bb ? ((bb.origin || '') + ' \\u21c4 ' + (bb.destination || '')) : '', current: '' });\n"
                    "        }\n"
                    "      } catch (e3) { /* never block saving */ }\n"
                    "      box.remove();\n"
                    "      render();")
        assert s.count(old_save) == 1, 'save anchor not found'
        s = s.replace(old_save, new_save)
        print('ux-fixes.js: save() now posts to review queue')
    open(p, 'w', encoding='utf-8').write(s)

    # ---------- 3) index.html : footer line + cache busts ----------
    p = 'index.html'
    s = open(p, encoding='utf-8').read()
    anchor = 'Contact: <a href="mailto:busjatri@zohomail.in">busjatri@zohomail.in</a></p>'
    if 'bjContrib' not in s:
        assert anchor in s, 'footer anchor not found'
        s = s.replace(anchor, anchor +
                      '\n      <p id="bjContrib" style="font-size:11px;color:var(--ink-dim,#777);margin:6px 0 0"></p>')
        print('index.html: contributor line added to footer')
    s = s.replace('js/extras.js?v=bj20260919b', 'js/extras.js?v=rpt20260920a')
    s = s.replace('js/ux-fixes.js?v=untimed20260920a', 'js/ux-fixes.js?v=rpt20260920a')
    open(p, 'w', encoding='utf-8').write(s)
    print('index.html: cache busts bumped')

    # ---------- 4) css ----------
    p = 'css/extras.css'
    s = open(p, encoding='utf-8').read()
    if '.rf-row select' not in s:
        s += ('\n/* report form: type select */\n'
              '.rf-row select{padding:8px 10px;border:1px solid var(--line);border-radius:8px;'
              'background:var(--surface);color:var(--ink);font-size:13px;min-height:42px;max-width:100%}\n')
        open(p, 'w', encoding='utf-8').write(s)
        print('extras.css: select styling added')

    p = 'css/ux-fixes.css'
    s = open(p, encoding='utf-8').read()
    if '.bj-timebox input.bj-name' not in s:
        s += ('\n/* add-time box: contributor name input */\n'
              '.bj-timebox input.bj-name{width:118px;text-align:left;font:600 13px var(--font-body,var(--font-body));}\n')
        open(p, 'w', encoding='utf-8').write(s)
        print('ux-fixes.css: name input width added')

    print('DONE (write=%s)' % args.write)

if __name__ == '__main__':
    main()
