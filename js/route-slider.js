/* private city route bilingual labels: EN/বাংলা toggle aware */
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

  function stopBnMap() {
    var map = {};
    var stops = window.STOPS;
    if (Array.isArray(stops)) {
      stops.forEach(function (p) {
        if (Array.isArray(p) && p.length > 1 && p[0] && p[1]) map[String(p[0]).trim()] = String(p[1]).trim();
      });
    }
    return map;
  }

  function enhanceRouteMapLanguage() {
    var map = stopBnMap();
    if (!Object.keys(map).length) return;
    document.querySelectorAll('.routemap .rm-name').forEach(function (el) {
      if (el.querySelector('.label-en')) return;
      var en = (el.textContent || '').trim();
      if (!en || !map[en]) return;
      el.innerHTML = '<span class="label-en">'+en+'</span><span class="label-bn">'+map[en]+'</span>';
    });
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
    var map = stopBnMap();
    var stops = Array.from(document.querySelectorAll('.routemap .rm-name')).map(function (x) {
      return (x.textContent || '').trim();
    }).filter(Boolean);
    var uniq = [];
    stops.forEach(function (s) { if (uniq.indexOf(s) < 0) uniq.push(s); });
    var stopHtml = uniq.length ? '<div class="private-stops"><div class="private-stops-title"><span class="label-en">Route stops</span><span class="label-bn">রুটের স্টপেজ</span></div><div class="private-stop-list">' +
      uniq.map(function (s, i) {
        var bn = map[s] || s;
        return '<span class="private-stop'+(i===0?' first':'')+(i===uniq.length-1?' last':'')+'"><span class="label-en">'+s+'</span><span class="label-bn">'+bn+'</span></span>';
      }).join('<span class="private-stop-arrow">›</span>') +
      '</div></div>' : '';
    var card = document.createElement('div');
    card.className = 'tt-card private-no-time';
    card.innerHTML =
      '<div class="tt-head"><div><div class="tt-title"><span class="label-en">Timetable</span><span class="label-bn">টাইম টেবিল</span></div><div class="tt-sub"><span class="label-en">schedule not listed · private route</span><span class="label-bn">সময়সূচি তালিকাভুক্ত নেই · বেসরকারি রুট</span></div></div><span class="private-na-pill"><span class="label-en">NO SCHEDULE</span><span class="label-bn">সময়সূচি নেই</span></span></div>' +
      '<div class="private-rail-wrap">' +
        '<div class="private-rail-cols"><span><span class="label-en">Departure</span><span class="label-bn">ছাড়ার সময়</span></span><span><span class="label-en">Ride</span><span class="label-bn">যাত্রা</span></span><span><span class="label-en">Arrival</span><span class="label-bn">পৌঁছানোর সময়</span></span></div>' +
        '<div class="private-rail-row"><div>—</div><div><i></i><span class="label-en">Not available</span><span class="label-bn">উপলভ্য নয়</span><i></i></div><div>—</div></div>' +
      '</div>' +
      '<div class="private-message"><strong>'+route+'</strong><br><span class="label-en">Official departure and arrival times are not listed yet. When a published timetable becomes available, the exact times can be added here.</span><span class="label-bn">সরকারি ছাড়ার ও পৌঁছানোর সময় এখনও তালিকাভুক্ত নেই। প্রকাশিত সময়সূচি পাওয়া গেলে সঠিক সময় এখানে যোগ করা যাবে।</span></div>' +
      stopHtml +
      '<p class="tt-note"><span class="label-en">No timing values have been estimated or invented for this private route.</span><span class="label-bn">এই বেসরকারি রুটের কোনো সময় অনুমান বা মনগড়া করে দেখানো হয়নি।</span></p>';
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
    enhanceRouteMapLanguage();
    initPrivateNoSchedule();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
