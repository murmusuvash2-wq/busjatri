/* BusJatri — legacy compatibility shim.
   Language state now belongs to js/lang.js / window.BJLang.
   Kept as a tiny bridge so older pages that still include this file do not
   create a second language controller. */
(function () {
  'use strict';
  if (!window.BJLang) return;
  window.setLang = function (lang) { return window.BJLang.setLang(lang); };
})();
