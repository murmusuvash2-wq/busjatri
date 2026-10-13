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
  function init() {
    document.querySelectorAll('.routemap, .chip-row.hscroll').forEach(initOne);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
