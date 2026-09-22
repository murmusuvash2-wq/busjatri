/* BusJatri — Bus Detail Page redesign (overrides app.js renderBus)
   Loaded AFTER app.js so function redefinition takes effect at call time.
   Depends on globals from app.js: BUSES, STOPS, DATA, esc, pn, busTypeBadge, icon, loadWeather */
var COMMUNITY_TIME_KEY = 'busjatri-community-times-v1';
function communityTimes() {
  try { return JSON.parse(localStorage.getItem(COMMUNITY_TIME_KEY) || '{}'); } catch (e) { return {}; }
}
function communityTimeKey(busId, stopIndex, direction) { return busId + '|' + stopIndex + '|' + direction; }
function normalizeCommunityTime(value) {
  var v = String(value || '').trim().replace('.', ':').toUpperCase();
  var m = v.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/);
  if (!m || Number(m[1]) < 1 || Number(m[1]) > 12 || Number(m[2]) > 59) return '';
  return Number(m[1]) + ':' + m[2] + ' ' + m[3];
}
function addCommunityTime(busId, stopIndex, direction, stopName) {
  var value = normalizeCommunityTime(window.prompt('Enter time, for example 11:30 AM'));
  if (!value) { window.alert('Please enter time like 11:30 AM.'); return; }
  var times = communityTimes();
  times[communityTimeKey(busId, stopIndex, direction)] = value;
  try { localStorage.setItem(COMMUNITY_TIME_KEY, JSON.stringify(times)); } catch (e) {}
  /* silently report the addition to the team (no email, no popup) */
  try {
    var bb = (typeof BUSES !== 'undefined' && BUSES && BUSES[busId]) || {};
    if (typeof sendReport === 'function') {
      sendReport({
        bus: bb.bus_name || busId, reg: bb.reg_no || '',
        route: (bb.origin || '') + ' \u21c4 ' + (bb.destination || ''),
        current: (direction === 'up' ? 'not available' : (bb.departure_time || '')),
        time: value,
        note: 'Stop: ' + (stopName || '?') + ' \u00b7 ' + (direction === 'up' ? 'outbound' : 'return'),
        page: location.href, bus_id: busId
      });
    }
  } catch (e) {}
  render();
}
function timeCell(stop, stopIndex, direction, busId) {
  var official = stop[direction + '_time'] || '';
  if (official) return '<span>' + esc(official) + '</span>';
  var userTime = communityTimes()[communityTimeKey(busId, stopIndex, direction)];
  if (userTime) return '<span class="community-time">' + esc(userTime) + '<small>User updated</small></span>';
  return '<button class="add-time-btn" onclick="addCommunityTime(\'' + esc(busId) + '\',' + stopIndex + ',\'' + direction + '\',\'' + esc(stop.name) + '\')">+ Add time</button>';
}

function fmtRegNo(r) {
  var m = String(r || '').trim().toUpperCase().match(/^([A-Z]{2})(\d{2}[A-Z]?)(\d{4})$/);
  return m ? (m[1] + ' ' + m[2] + ' ' + m[3]) : String(r || '').trim();
}
function buildBusCopyText(b, stops) {
  var E = String.fromCharCode;
  var BUS = E(0xD83D,0xDE8C), NUM = E(0xD83D,0xDD22), PHONE = E(0xD83D,0xDCDE), PIN = E(0xD83D,0xDCCD), STOP = E(0xD83D,0xDE8F);
  var DOT = E(0xB7), ARROW = E(0x2192), DASH = E(0x2014), NL = E(10);
  var L = [];
  L.push(BUS + ' ' + (b.bus_name || ''));
  if (b.reg_no) L.push(NUM + ' ' + fmtRegNo(b.reg_no));
  if (b.contact_number && b.contact_number !== 'Not Available !') L.push(PHONE + ' ' + b.contact_number);
  if (b.origin && b.destination) L.push(PIN + ' ' + pn(b.origin) + ' ' + ARROW + ' ' + pn(b.destination) + (b.departure_time ? ' ' + DOT + ' ' + b.departure_time : ''));
  var timed = stops.filter(function (s) { return s.up_time; }).map(function (s) { return pn(s.name) + ' ' + s.up_time; });
  if (!timed.length) timed = stops.filter(function (s) { return s.down_time; }).map(function (s) { return pn(s.name) + ' ' + s.down_time; });
  if (timed.length) { L.push(''); L.push(STOP + ' ' + timed.join(' ' + DOT + ' ')); }
  L.push('');
  L.push(DASH + ' BusJatri.in ' + BUS);
  return L.join(NL);
}
var BJ_COPY_ICON = '<svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#b8791f" aria-hidden="true"><path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1Zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2Zm0 16H8V7h11v14Z"/></svg>';
function copyBusDetails(btn) {
  var txt = window.BJ_COPY_TEXT || '';
  if (!txt || !btn) return;
  function done() {
    btn.style.background = '#2b7a3e'; btn.style.borderColor = '#2b7a3e';
    btn.innerHTML = '<svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#fff" aria-hidden="true"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z"/></svg>';
    setTimeout(function () {
      btn.style.background = 'linear-gradient(135deg,#fdf6e6,#f7ecd4)'; btn.style.borderColor = '#e5dcc9';
      btn.innerHTML = BJ_COPY_ICON;
    }, 2000);
  }
  function fallback() {
    try {
      var ta = document.createElement('textarea');
      ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.focus(); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta); done();
    } catch (e) {}
  }
  if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(txt).then(done, fallback); }
  else { fallback(); }
}

async function renderBus(el, id) {
  id = id.split('?')[0];
  const b = typeof loadFullBus === 'function' ? await loadFullBus(id) : BUSES[id];
  if (!b) {
    el.innerHTML = '<div class="container" style="padding:40px"><div class="empty-state">' + icon('alert') + '<p>Bus not found.</p></div><div class="back-btn" onclick="location.hash=\'#/\'">' + icon('chevronLeft') + ' Back</div></div>';
    return;
  }
  const stops = b.stoppage_pages || b.stoppages || [];
  const INITIAL = 8;
  const showAll = location.hash.includes('full=1');
  const visible = showAll ? stops : stops.slice(0, INITIAL);
  const returnDeparture = stops.slice().reverse().find(s => s.down_time)?.down_time || '';
  const returnArrival = stops.find(s => s.down_time)?.down_time || '';

  const stopNames = stops.map(s => s.name).filter(Boolean);
  let mapUrl = '';
  if (stopNames.length >= 2) {
    const o = encodeURIComponent(stopNames[0] + ', West Bengal');
    const d2 = encodeURIComponent(stopNames[stopNames.length - 1] + ', West Bengal');
    const wp = stopNames.slice(1, -1).slice(0, 8).map(n => encodeURIComponent(n + ', West Bengal')).join('|');
    mapUrl = 'https://www.google.com/maps/dir/?api=1&origin=' + o + '&destination=' + d2 + (wp ? '&waypoints=' + wp : '') + '&travelmode=driving';
  } else if (b.origin && b.destination) {
    mapUrl = 'https://www.google.com/maps/dir/?api=1&origin=' + encodeURIComponent(b.origin + ', West Bengal') + '&destination=' + encodeURIComponent(b.destination + ', West Bengal') + '&travelmode=driving';
  }

  const stopHTML = visible.map(function(s, i) {
    var isEnd = i === 0 || i === visible.length - 1;
    var stn = (STOPS[s.name] || {}).nearest_station;
    var stnBadge = stn ? '<span class="rail">Railway: ' + esc(stn.name) + (stn.code ? ' (' + esc(stn.code) + ')' : '') + ' \u00b7 ~' + stn.km + ' km</span>' : '';
    var upT = timeCell(s, i, 'up', id);
    var dnT = timeCell(s, i, 'down', id);
    return '<div class="stop-row ' + (isEnd ? 'end' : '') + '"><span class="stop-dot"></span><span class="stop-name">' + esc(pn(s.name)) + stnBadge + '</span><span class="stop-times"><span class="time-out">' + upT + '</span><span class="time-in">' + dnT + '</span></span></div>';
  }).join('');

  var showMoreBtn = '';
  if (!showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '?full=1\'">Show all ' + stops.length + ' stops \u21d3</button>';
  } else if (showAll && stops.length > INITIAL) {
    showMoreBtn = '<button class="show-all" onclick="location.hash=\'#/bus/' + encodeURIComponent(id) + '\'">Show less \u21d1</button>';
  }

  window.BJ_SHARE = { bus: b.bus_name, reg: b.reg_no || '', org: pn(b.origin), dest: pn(b.destination),
    dep: b.departure_time || '', stops: stops.map(function (s) { return { name: pn(s.name), up: s.up_time || '', down: s.down_time || '' }; }) };
  window.BJ_COPY_TEXT = buildBusCopyText(b, stops);
  /* approx travel time (kitna time lagega) — only when both dep & arr are known */
  var travelItem = (function () {
    function t2m(t) {
      if (!t) return null;
      var m = /^(\d{1,2}):(\d{2})\s*(AM|PM)?/i.exec(String(t).trim());
      if (!m) return null;
      var h = +m[1], mi = +m[2], s = (m[3] || '').toUpperCase();
      if (mi > 59) return null;
      if (s === 'PM' && h < 12) h += 12;
      if (s === 'AM' && h === 12) h = 0;
      if (h > 23) return null;
      return h * 60 + mi;
    }
    var d1 = t2m(b.departure_time), d2 = t2m(b.arrival_time);
    if (d1 == null || d2 == null) return '';
    var dur = d2 < d1 ? d2 + 1440 - d1 : d2 - d1;
    if (dur < 10 || dur > 900) return '';
    var h = Math.floor(dur / 60), m2 = dur % 60;
    var txt = (h ? h + 'h ' : '') + (h ? String(m2).padStart(2, '0') : m2) + 'm';
    return '<div class="info-item"><div class="lbl">Travel time</div><div class="val">\u2248 ' + txt + '</div></div>';
  })();
  el.innerHTML =
    '<div class="container" style="padding-top:22px;padding-bottom:40px">' +
      '<div class="back-btn" onclick="history.length>1?history.back():location.hash=\'#/\'">' + icon('chevronLeft') + ' <span class="label-en">Back</span></div>' +
      '<div class="bus-head">' +
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px">' +
        '<h2 style="flex:1 1 auto;min-width:0">' + esc(b.bus_name) + (b.reg_no ? ' <span class="reg">' + esc(b.reg_no) + '</span>' : '') + ' ' + busTypeBadge(b.bus_type) + '</h2>' +
        '<button onclick="copyBusDetails(this)" title="Copy bus details" aria-label="Copy bus details" style="flex:0 0 auto;width:42px;height:42px;border-radius:12px;border:1px solid #e5dcc9;background:linear-gradient(135deg,#fdf6e6,#f7ecd4);display:flex;align-items:center;justify-content:center;cursor:pointer;margin-top:2px;padding:0">' + BJ_COPY_ICON + '</button>' +
      '</div>' +
        '<div class="route-line">' + icon('bus') + ' ' + esc(pn(b.origin)) + ' \u21c4 ' + esc(pn(b.destination)) + '</div>' +
        '<div class="info-grid">' +
          (b.departure_time ? '<div class="info-item"><div class="lbl">Departure</div><div class="val">' + esc(b.departure_time) + '</div></div>' : '') +
          (b.arrival_time ? '<div class="info-item"><div class="lbl">Arrival</div><div class="val">' + esc(b.arrival_time) + '</div></div>' : '') +
          travelItem +
          '<div class="info-item"><div class="lbl">Stops</div><div class="val">' + (stops.length || b.total_stoppage_pages || 0) + '</div></div>' +
          (b.fare ? '<div class="info-item"><div class="lbl">Fare</div><div class="val">' + esc(b.fare) + '</div></div>' : '') +
          (b.operator ? '<div class="info-item"><div class="lbl">Operator</div><div class="val">' + esc(b.operator) + '</div></div>' : '') +
          (b.depot_name ? '<div class="info-item"><div class="lbl">Depot</div><div class="val">' + esc(b.depot_name) + '</div></div>' : '') +
          (b.contact_number && b.contact_number !== 'Not Available !' ? '<div class="info-item"><div class="lbl">Contact</div><div class="val"><a href="tel:' + esc(b.contact_number) + '">' + esc(b.contact_number) + '</a></div></div>' : '') +
        '</div>' +
        (returnDeparture ? '<div class="return-journey"><strong>Return journey</strong><span>' + esc(pn(b.destination)) + ' → ' + esc(pn(b.origin)) + '</span><span>Departs ' + esc(returnDeparture) + (returnArrival ? ' · arrives around ' + esc(returnArrival) : '') + '</span></div>' : '') +
      '</div>' +
      '<div class="wa-row">' +
        (mapUrl ? '<a class="map-btn" href="' + mapUrl + '" target="_blank" rel="noopener" title="Open route in Google Maps" aria-label="Open route in Google Maps">' + '<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" fill="currentColor"><path fill-rule="evenodd" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>' + '</a>' : '') +
        '<a class="wa-btn" href="javascript:void(0)" onclick="shareBusWhatsApp()" title="Share on WhatsApp" aria-label="Share on WhatsApp">' + '<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.347-.347.52-.52.174-.174.232-.298.347-.497.115-.198.057-.371-.058-.52-.115-.148-.669-1.611-.916-2.207-.244-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413"/></svg>' + '</a>' +
        '<a class="fb-btn" href="javascript:void(0)" onclick="shareBusFacebook()" title="Share on Facebook" aria-label="Share on Facebook">' + '<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>' + '</a>' +
        '<a class="report-btn" href="javascript:void(0)" onclick="toggleReport(this)" title="Report issue" aria-label="Report issue" data-id="' + esc(id) + '" data-bus="' + esc(b.bus_name) + '" data-reg="' + esc(b.reg_no || '') + '" data-org="' + esc(pn(b.origin)) + '" data-dest="' + esc(pn(b.destination)) + '" data-dep="' + esc(b.departure_time || '') + '">' + '<svg viewBox="0 0 24 24" style="width:18px;height:18px;flex:0 0 auto" aria-hidden="true" fill="currentColor"><path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z"/></svg>' + '</a>' +
      '</div>' +
      (b.destination && b.destination !== '\u2014' ? '<div class="weather-card" id="weatherCard" data-dest="' + esc(b.destination) + '"><div class="lbl">Weather in ' + esc(b.destination) + ' (now)</div><div class="val" id="weatherVal">Loading\u2026</div></div>' : '') +
      (stops.length ? '<h3 class="section-title" style="margin-top:22px">' + icon('ticket') + ' <span class="label-en">Route Timetable</span></h3><div class="schedule-legend"><span><i class="legend-dot outbound"></i> From ' + esc(pn(b.origin)) + '</span><span><i class="legend-dot inbound"></i> Return to ' + esc(pn(b.origin)) + '</span><span class="community-note">Times marked “User updated” are community-submitted.</span></div><div class="schedule-table"><div class="schedule-head"><span>Stop</span><span>Outbound</span><span>Return</span></div><div class="stop-list">' + stopHTML + showMoreBtn + '</div></div>' : '<p style="color:var(--ink-dim);margin-top:12px">Stoppage details not available.</p>') +
      '<p style="font-size:12px;color:var(--ink-dim);margin:10px 0 0">Data updated: ' + esc((DATA.meta||{}).last_updated || '') + '</p>' +
    '</div>';
  loadWeather();
}
