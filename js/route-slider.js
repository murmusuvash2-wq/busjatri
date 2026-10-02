/* BusJatri route map / chip-row horizontal slider (UX audit 2026-09-19).
   Adds swipe scrolling + prev/next arrow buttons to .routemap and
   .chip-row.hscroll containers. Arrows appear only when the content
   actually overflows. No dependencies. */
(function () {
  function makeArr(el, dir) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'hscroll-arr ' + (dir < 0 ? 'hsa-prev' : 'hsa-next');
    b.setAttribute('aria-label', dir < 0 ? 'Scroll left' : 'Scroll right');
    b.textContent = dir < 0 ? '\u276E' : '\u276F';
    b.addEventListener('click', function (e) {
      e.preventDefault();
      el.scrollBy({ left: dir * Math.max(120, el.clientWidth * 0.7), behavior: 'smooth' });
    });
    el.parentNode.insertBefore(b, el);
    return b;
  }
  function initOne(el) {
    if (el.__bjSlider) return;
    el.__bjSlider = 1;
    var prev = makeArr(el, -1);
    var next = makeArr(el, 1);
    function upd() {
      var over = el.scrollWidth - el.clientWidth > 8;
      prev.style.display = (over && el.scrollLeft > 4) ? 'flex' : 'none';
      next.style.display = (over && el.scrollLeft < el.scrollWidth - el.clientWidth - 4) ? 'flex' : 'none';
    }
    el.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    if (typeof MutationObserver !== 'undefined') {
      new MutationObserver(upd).observe(el, { childList: true, subtree: true });
    }
    upd();
  }

  function privateNoSchedule() {
    if (!document.querySelector('.badge-priv')) return;
    var sec = Array.from(document.querySelectorAll('.seo-section')).find(function (s) {
      var h = s.querySelector('.section-title');
      return h && /Scheduled Departures/i.test(h.textContent || '');
    });
    if (!sec || sec.__bjPrivateRail) return;
    sec.__bjPrivateRail = 1;
    var row = sec.querySelector('.bus-row');
    var hero = document.querySelector('.seo-hero h1');
    var route = hero ? hero.textContent.replace(/\s+/g,' ').trim() : 'This private bus route';
    var stops = Array.from(document.querySelectorAll('.routemap .rm-name')).map(function (x) {
      return (x.textContent || '').trim();
    }).filter(Boolean);
    var uniq = [];
    stops.forEach(function (s) { if (uniq.indexOf(s) < 0) uniq.push(s); });
    var stopHtml = uniq.length ? '<div class="private-stops"><div class="private-stops-title">Route stops</div><div class="private-stop-list">' +
      uniq.map(function (s, i) { return '<span class="private-stop'+(i===0?' first':'')+(i===uniq.length-1?' last':'')+'">'+s+'</span>'; }).join('<span class="private-stop-arrow">›</span>') +
      '</div></div>' : '';
    var card = document.createElement('div');
    card.className = 'tt-card private-no-time';
    card.innerHTML =
      '<div class="tt-head"><div><div class="tt-title">Timetable</div><div class="tt-sub">schedule not listed · private route</div></div><span class="private-na-pill">NO SCHEDULE</span></div>' +
      '<div class="private-rail-wrap">' +
        '<div class="private-rail-cols"><span>Departure</span><span>Ride</span><span>Arrival</span></div>' +
        '<div class="private-rail-row"><div>—</div><div><i></i><span>Not available</span><i></i></div><div>—</div></div>' +
      '</div>' +
      '<div class="private-message"><strong>'+route+'</strong><br>Official departure and arrival times are not listed yet. When a published timetable becomes available, the exact times can be added here.</div>' +
      stopHtml +
      '<p class="tt-note">No timing values have been estimated or invented for this private route.</p>';
    if (row) row.remove();
    sec.appendChild(card);
    var mapSec = Array.from(document.querySelectorAll('.seo-section')).find(function (s) {
      var h=s.querySelector('.section-title'); return h && /^Route Map$/i.test((h.textContent||'').trim());
    });
    if (mapSec) mapSec.style.display='none';
  }
  function initPrivateNoSchedule() { privateNoSchedule(); }

  function init() {
    document.querySelectorAll('.routemap, .chip-row.hscroll').forEach(initOne);
    initPrivateNoSchedule();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
