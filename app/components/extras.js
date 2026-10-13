/* BusJatri Extras — WhatsApp share, geolocation, report time, admin, static-page helpers */

/* ---------- Theme (static pages) ---------- */
function toggleThemeStatic() {
  var cur = document.documentElement.getAttribute('data-theme') ||
    (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  var next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('bj-theme', next); } catch (e) {}
  updateThemeIconStatic(next);
}
function updateThemeIconStatic(theme) {
  var btn = document.getElementById('themeBtn');
  if (!btn) return;
  btn.innerHTML = theme === 'dark'
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
}
(function () {
  var saved = null;
  try { saved = localStorage.getItem('bj-theme'); } catch (e) {}
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  var eff = saved || (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  updateThemeIconStatic(eff);
})();

/* ---------- WhatsApp Share — bus time + site link ---------- */
function shareWhatsApp(busName, origin, destination, departure, stops) {
  var msg = "BusJatri — West Bengal Bus Timetable\n\n";
  msg += "Bus: " + (busName || "—") + "\n";
  msg += "Route: " + (origin || "—") + " → " + (destination || "—") + "\n";
  if (departure) msg += "Departure: " + departure + "\n";
  if (stops) msg += "Stops: " + stops + "\n";
  msg += "\nView this bus timetable:\n" + window.location.href;
  msg += "\n\nMore buses on BusJatri (বাস যাত্রী)";
  window.open("https://wa.me/?text=" + encodeURIComponent(msg), "_blank");
}
function shareTwitter(data) {
  var text = (data && data.bus ? data.bus + " — " : "") +
    (data && data.org || "—") + " → " + (data && data.dest || "—");
  if (data && data.dep) text += " · Departs " + data.dep;
  window.open("https://x.com/intent/post?text=" + encodeURIComponent(text) + "&url=" + encodeURIComponent(window.location.href), "_blank", "noopener");
}

/* ---------- Geolocation Auto-Detect — prefill "From" field ---------- */
function detectLocation() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function (pos) {
    fetch("https://nominatim.openstreetmap.org/reverse?lat=" + pos.coords.latitude + "&lon=" + pos.coords.longitude + "&format=json&accept-language=en")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var a = data.address || {};
        var city = a.city || a.town || a.village || a.county || a.state_district;
        if (city) {
          var inputs = document.querySelectorAll(".search-field input");
          if (inputs[0] && !inputs[0].value) {
            inputs[0].value = city;
            var hint = document.querySelector(".geo-hint");
            if (hint) {
              var c = hint.querySelector(".geo-city");
              if (c) c.textContent = city;
              hint.classList.add("show");
            }
          }
        }
      })
      .catch(function () { /* silent — detection is best-effort only */ });
  }, function () { /* denied or failed — ignore */ }, { timeout: 8000 });
}

/* ---------- Contact Form — opens user's email client ---------- */
function sendContact() {
  var name = (document.getElementById("cName") || {}).value || "";
  var email = (document.getElementById("cEmail") || {}).value || "";
  var subject = (document.getElementById("cSubject") || {}).value || "Feedback";
  var message = (document.getElementById("cMessage") || {}).value || "";
  var body = "Name: " + name + "\nEmail: " + email + "\n\n" + message;
  var url = "mailto:busjatri@zohomail.in?subject=" + encodeURIComponent("[BusJatri] " + subject) + "&body=" + encodeURIComponent(body);
  var ok = document.getElementById("contactSuccess");
  if (ok) ok.style.display = "flex";
  window.location.href = url;
}

/* ---------- Report / Suggest - on bus detail pages ----------
   Submits to the BusJatri receiver (Google Apps Script web app).
   REPORT_FORM.action holds the web-app URL once deployed.
   Types: time-report | bus-stopped | route-change | add-time (from the
   + mini box in ux-fixes.js). No email, no login, no popup. */
var REPORT_FORM = { action: "https://script.google.com/macros/s/AKfycby3uePQMRoPwXg-7rWRgtF5TIyHe7e1brhGscIC_t_CtzVJiHke8DOf3-Ff5zMk1VZv/exec" };
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
    '<div class="rf-title">' + (bn ? "\u0995\u09bf\u099b\u09c1 \u09ad\u09c1\u09b2? \u099c\u09be\u09a8\u09bf\u09df\u09c7 \u09a6\u09bf\u09a8:" : "Something wrong? Tell us:") + '</div>' +
    '<div class="rf-row">' +
      '<select id="bjReportType" aria-label="Report type">' +
        '<option value="bus-stopped">' + (bn ? "\u09ac\u09be\u09b8 \u098f\u0996\u09a8 \u099a\u09b2\u09c7 \u09a8\u09be" : "Bus no longer runs") + '</option>' +
        '<option value="route-change">' + (bn ? "\u09b0\u09c1\u099f \u09ac\u09a6\u09b2\u09c7 \u0997\u09c7\u099b\u09c7" : "Route has changed") + '</option>' +
      '</select>' +
      '<input type="text" id="bjReportNote" placeholder="' + (bn ? "\u09ae\u09a8\u09cd\u09a4\u09ac\u09cd\u09af (\u0990\u099a\u09cd\u099b\u09bf\u0995)" : "Note (optional)") + '" maxlength="140">' +
      '<input type="text" id="bjReportName" placeholder="' + (bn ? "\u09a8\u09be\u09ae (\u0990\u099a\u09cd\u099b\u09bf\u0995)" : "Name (optional)") + '" maxlength="30" value="' + savedName.replace(/"/g, '&quot;') + '">' +
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

/* ---------- Footer contributors credit line ---------- */
function loadContributors() {
  var el = document.getElementById("bjContrib");
  if (!el) return;
  fetch("data/contributors.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (list) {
      if (!list || !list.length) return;
      while (el.firstChild) el.removeChild(el.firstChild);
      el.appendChild(document.createTextNode("\u2764 Times improved by: "));
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

/* ---------- Admin Dashboard (demo actions) ---------- */
function adminUpdate(btn, msg) {
  if (!btn) return;
  var old = btn.textContent;
  btn.textContent = "✓ Saved";
  btn.disabled = true;
  setTimeout(function () { btn.textContent = old; btn.disabled = false; }, 1600);
  if (msg) {
    var bar = document.getElementById("adminMsg");
    if (bar) { bar.textContent = msg; bar.style.display = "block"; setTimeout(function () { bar.style.display = "none"; }, 2600); }
  }
}
function approveReport(btn) {
  if (!btn) return;
  var row = btn.closest(".admin-report-row");
  btn.textContent = "Approved ✓";
  btn.disabled = true;
  if (row) { row.style.opacity = ".55"; }
}

/* ---------- AdSense zone activation (when ads script present) ---------- */
(function () {
  if (window.adsbygoogle) {
    document.querySelectorAll(".ad-zone").forEach(function (z) { z.classList.add("active"); });
  }
})();

/* ---------- Auto-detect location on home page ---------- */
document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector(".search-field")) detectLocation();
  loadContributors();
});
