#!/usr/bin/env python3
"""Bus page UI changes (Murmu's requests):
1. Report form: bus-level issues only (bus stopped / route changed), proper
   English + Bengali text (no Hinglish), no time input. Short thank-you.
2. + Add time box: 'Name (optional)' label EN/BN, short thank-you toast on save.
3. WhatsApp & Facebook share: full text - bus name, route, all stoppages with
   outbound/return times, site link at bottom. Same content on both.
4. Cache-bust bump for extras.js / ux-fixes.js / bus-page.js."""
import io

EXTRAS_NEW = r"""function toggleReport(btn) {
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
    '<div class="rf-title">' + (bn ? "\u0995\u09bf\u099b\u09c1 \u09ad\u09c1\u09b2? \u099c\u09be\u09a8\u09bf\u09df\u09c7 \u09a6\u09bf\u09a8:" : "Something wrong? Tell us:") + '</div>' +
    '<div class="rf-row">' +
      '<select id="bjReportType" aria-label="Report type">' +
        '<option value="bus-stopped">' + (bn ? "\u09ac\u09be\u09b8 \u098f\u0996\u09a8 \u099a\u09b2\u09c7 \u09a8\u09be" : "Bus no longer runs") + '</option>' +
        '<option value="route-change">' + (bn ? "\u09b0\u09c1\u099f \u09ac\u09a6\u09b2\u09c7 \u0997\u09c7\u099b\u09c7" : "Route has changed") + '</option>' +
      '</select>' +
      '<input type="text" id="bjReportNote" placeholder="' + (bn ? "\u09ae\u09a8\u09cd\u09a4\u09ac\u09cd\u09af (\u0990\u099a\u09cd\u099b\u09bf\u0995)" : "Note (optional)") + '" maxlength="140">' +
      '<input type="text" id="bjReportName" placeholder="' + (bn ? "\u09a8\u09be\u09ae (\u0990\u099a\u09cd\u099b\u09bf\u0995)" : "Name (optional)") + '" maxlength="30" value="' + savedName.replace(/"/g, '"') + '">' +
      '<button class="rf-send" onclick="submitReport()">Send</button>' +
    '</div>' +
    '<div class="rf-done" id="bjReportDone">\u2713 ' + (bn ? "\u0985\u09ac\u09a6\u09be\u09a8\u09c7\u09b0 \u099c\u09a8\u09cd\u09af \u09a7\u09a8\u09cd\u09af\u09ac\u09be\u09a6!" : "Thank you for contributing!") + '</div>';
  var row = btn.closest(".wa-row");
  if (row && row.parentNode) row.parentNode.insertBefore(f, row.nextSibling);
  var n = document.getElementById("bjReportNote");
  if (n) n.focus();
}
function submitReport() {
  var c = REPORT_CTX || {};
  var sel = document.getElementById("bjReportType");
  var type = sel ? sel.value : "bus-stopped";
  var note = (document.getElementById("bjReportNote") || {}).value || "";
  var name = (document.getElementById("bjReportName") || {}).value || "";
  try { if (name) localStorage.setItem("bj-name", name); } catch (e) {}
  var payload = {
    type: type, bus: c.bus, reg: c.reg, route: (c.org || "") + " \u21c4 " + (c.dest || ""),
    current: c.dep, time: "", note: note, page: location.href,
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

/* ---------- Bus share (WhatsApp / Facebook) - full stoppage list ---------- */
function bjBuildBusText() {
  var s = window.BJ_SHARE;
  if (!s) return "";
  var msg = "BusJatri \u2014 West Bengal Bus Timetable\n\n";
  msg += "Bus: " + (s.bus || "\u2014") + (s.reg ? " (" + s.reg + ")" : "") + "\n";
  msg += "Route: " + (s.org || "\u2014") + " \u21c4 " + (s.dest || "\u2014") + "\n";
  if (s.dep) msg += "Departure: " + s.dep + "\n";
  if (s.stops && s.stops.length) {
    msg += "\nStoppages (outbound / return):\n";
    s.stops.forEach(function (st, i) {
      msg += (i + 1) + ". " + st.name + " \u2014 " + (st.up || "\u2014") + " / " + (st.down || "\u2014") + "\n";
    });
  }
  msg += "\nView full timetable:\n" + location.href;
  msg += "\n\nMore buses on BusJatri (\u09ac\u09be\u09b8 \u09af\u09be\u09a4\u09cd\u09b0\u09c0)";
  return msg;
}
function shareBusWhatsApp() {
  var msg = bjBuildBusText(); if (!msg) return;
  window.open("https://wa.me/?text=" + encodeURIComponent(msg), "_blank");
}
function shareBusFacebook() {
  var msg = bjBuildBusText(); if (!msg) return;
  window.open("https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(location.href) + "&quote=" + encodeURIComponent(msg), "_blank", "noopener");
}

"""

FB_BTN = (r"""'<a class="wa-btn" href="javascript:void(0)" onclick="shareBusWhatsApp()">' + icon('waves') + ' <span class="label-en">Share on WhatsApp</span></a>' +
        '<a class="wa-btn" href="javascript:void(0)" onclick="shareBusFacebook()"><svg viewBox="0 0 24 24" style="width:16px;height:16px;flex:0 0 auto" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7h2.4l.4-3h-2.8V9.1c0-.9.3-1.5 1.6-1.5h1.3V4.9c-.3 0-1.2-.1-2.2-.1-2.2 0-3.7 1.3-3.7 3.8V11H8.2v3h2.3v7h3z"/></svg> <span class="label-en">Share on Facebook</span></a>' +
""")

def main():
    # ---------- extras.js ----------
    s = io.open('js/extras.js', encoding='utf-8').read()
    if 'shareBusFacebook' in s:
        print('extras.js: already patched')
    else:
        start = s.index('function toggleReport(btn) {')
        end = s.index('/* ---------- Footer contributors credit line ---------- */')
        s = s[:start] + EXTRAS_NEW + s[end:]
        io.open('js/extras.js', 'w', encoding='utf-8').write(s)
        print('extras.js: report form rebuilt + share helpers added')

    # ---------- bus-page.js ----------
    b = io.open('js/bus-page.js', encoding='utf-8').read()
    if 'BJ_SHARE' in b:
        print('bus-page.js: already patched')
    else:
        a_head = "  el.innerHTML =\n    '<div class=\"container\" style=\"padding-top:22px;padding-bottom:40px\">' +"
        assert b.count(a_head) == 1, 'render head anchor: %d' % b.count(a_head)
        share_line = ("  window.BJ_SHARE = { bus: b.bus_name, reg: b.reg_no || '', org: pn(b.origin), dest: pn(b.destination),\n"
                      "    dep: b.departure_time || '', stops: stops.map(function (s) { return { name: pn(s.name), up: s.up_time || '', down: s.down_time || '' }; }) };\n")
        b = b.replace(a_head, share_line + a_head)
        bs = b.index("'<a class=\"wa-btn\"")
        be = b.index("Share on WhatsApp</span></a>' +") + len("Share on WhatsApp</span></a>' +")
        b = b[:bs] + FB_BTN.rstrip('\n') + b[be:]
        a_rep = '>✏ <span class="label-en">Report wrong time</span></a>'
        assert b.count(a_rep) == 1, 'report label anchor: %d' % b.count(a_rep)
        b = b.replace(a_rep, '>✏ <span class="label-en">Report issue</span><span class="label-bn">\\u09b0\\u09bf\\u09aa\\u09cb\\u09b0\\u09cd\\u099f \\u0995\\u09b0\\u09c1\\u09a8</span></a>')
        io.open('js/bus-page.js', 'w', encoding='utf-8').write(b)
        print('bus-page.js: share buttons + BJ_SHARE + report label done')

    # ---------- ux-fixes.js ----------
    u = io.open('js/ux-fixes.js', encoding='utf-8').read()
    if 'window.bjToast' in u:
        print('ux-fixes.js: already patched')
    else:
        a_box = '  function openBjTimeBox(busId, stopIndex, direction, existing) {'
        assert u.count(a_box) == 1, 'timebox anchor: %d' % u.count(a_box)
        toast_fn = ("""  window.bjToast = function (msg) {
    var d = document.createElement('div');
    d.textContent = msg;
    d.style.cssText = 'position:fixed;left:50%;bottom:84px;transform:translate(-50%,10px);background:#1c2333;color:#fff;padding:10px 18px;border-radius:12px;font-size:13.5px;font-weight:600;box-shadow:0 8px 22px rgba(0,0,0,.28);opacity:0;transition:opacity .25s,transform .25s;z-index:99999;max-width:88vw;text-align:center;pointer-events:none';
    document.body.appendChild(d);
    requestAnimationFrame(function () { d.style.opacity = '1'; d.style.transform = 'translate(-50%,0)'; });
    setTimeout(function () { d.style.opacity = '0'; setTimeout(function () { d.remove(); }, 350); }, 2600);
  };

""")
        u = u.replace(a_box, toast_fn + a_box)
        a_save = "      } catch (e3) { /* never block saving */ }\n      box.remove();\n      render();\n    }"
        assert u.count(a_save) == 1, 'save anchor: %d' % u.count(a_save)
        u = u.replace(a_save, "      } catch (e3) { /* never block saving */ }\n      box.remove();\n      render();\n      try { bjToast((typeof LANG !== 'undefined' && LANG === 'bn') ? '\\u0985\\u09ac\\u09a6\\u09be\\u09a8\\u09c7\\u09b0 \\u099c\\u09a8\\u09cd\\u09af \\u09a7\\u09a8\\u09cd\\u09af\\u09ac\\u09be\\u09a6!' : 'Thank you for contributing!'); } catch (e4) {}\n    }")
        a_name = "'<input type=\"text\" class=\"bj-name\" placeholder=\"Naam (optional)\" maxlength=\"30\" aria-label=\"name\">' +"
        assert u.count(a_name) == 1, 'name anchor: %d' % u.count(a_name)
        u = u.replace(a_name, "'<input type=\"text\" class=\"bj-name\" placeholder=\"' + (typeof LANG !== 'undefined' && LANG === 'bn' ? '\\u09a8\\u09be\\u09ae (\\u0990\\u099a\\u09cd\\u099b\\u09bf\\u0995)' : 'Name (optional)') + '\" maxlength=\"30\" aria-label=\"name\">' +")
        io.open('js/ux-fixes.js', 'w', encoding='utf-8').write(u)
        print('ux-fixes.js: toast + EN/BN labels done')

    # ---------- index.html cache-bust ----------
    h = io.open('index.html', encoding='utf-8').read()
    for old, new in [('js/extras.js?v=rpt20260920b', 'js/extras.js?v=rpt20260920c'),
                     ('js/ux-fixes.js?v=rpt20260920a', 'js/ux-fixes.js?v=rpt20260920c'),
                     ('js/bus-page.js?v=bj20260919b', 'js/bus-page.js?v=bj20260920c')]:
        if new in h:
            continue
        assert h.count(old) == 1, 'version anchor %s: %d' % (old, h.count(old))
        h = h.replace(old, new)
    io.open('index.html', 'w', encoding='utf-8').write(h)
    print('index.html: cache-busts bumped')

if __name__ == '__main__':
    main()
