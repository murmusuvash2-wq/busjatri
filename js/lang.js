/* BusJatri central language system — 2026-10-05
   One source of truth for Bengali UI state and English -> Bengali place names.
   Data JSON stays English; translation is presentation-only.
*/
(function (w, d) {
  'use strict';
  if (w.BJLang) return;

  var PLACES = {
    'Bankura':'বাঁকুড়া','Digha':'দীঘা','Kolkata':'কলকাতা','Medinipur':'মেদিনীপুর',
    'Bardhaman':'বর্ধমান','Burdwan':'বর্ধমান','Kharagpur':'খড়্গপুর','Siliguri':'শিলিগুড়ি','Jalpaiguri':'জলপাইগুড়ি','Jalpaiguri Bypass':'জলপাইগুড়ি বাইপাস','Sitai':'সিতাই','Silda':'শিলদা',
    'Barjora':'বড়জোড়া','Beliatore':'বেলিয়াতোড়','Adra':'আদ্রা','Arsha':'আর্শা','Baghmundi':'বাঘমুন্ডি',
    'Belda':'বেলদা','Binpur':'বিনপুর','Budbud':'বুদবুদ','Chhatna':'ছাতনা','Chittaranjan':'চিত্তরঞ্জন',
    'Dainhat':'দাঁইহাট','Dantan':'দাঁতন','Debra':'দেবরা','Andal':'অন্ডাল',
    'Darjeeling':'দার্জিলিং','Kalimpong':'কালিম্পং','Islampur':'ইসলামপুর','Panitanki':'পানিট্যাঙ্কি',
    'Cooch Behar':'কোচবিহার','Coach Behar':'কোচবিহার','Coochbehar':'কোচবিহার','Koch Bihar':'কোচবিহার',
    'Mainaguri':'ময়নাগুড়ি','Moynaguri':'ময়নাগুড়ি','Dhupguri':'ধূপগুড়ি','Falakata':'ফালাকাটা',
    'Alipurduar':'আলিপুরদুয়ার','Bagdogra':'বাগডোগরা','Fulbari':'ফুলবাড়ি','Fatapukur':'ফাটাপুকুর',
    'Salugara':'সালুগাড়া','Sevoke':'সেবক','Coronation Bridge':'করোনেশন ব্রিজ','Bagrakot':'বাগরাকোট',
    'Oodlabari':'ওদলাবাড়ি','Odlabari':'ওদলাবাড়ি','Damdim':'ডামডিম','Malbazar':'মালবাজার',
    'Kishanganj':'কিশনগঞ্জ','Dalkhola':'ডালখোলা','Itahar':'ইটাহার','Gangarampur':'গঙ্গারামপুর',
    'Buniadpur':'বুনিয়াদপুর','Tapan':'তপন','Samsi':'সামসি','Chanchal':'চাঁচল',
    'Dhubulia':'ধুবুলিয়া','Phulia':'ফুলিয়া','Shantipur':'শান্তিপুর','Beldanga':'বেলডাঙা',
    'Farakka':'ফারাক্কা','Gazole':'গাজোল','Kaliachak':'কালিয়াচক','Sujapur':'সুজাপুর',
    'Baharampur':'বহরমপুর','Madhyamgram':'মধ্যমগ্রাম','Amdanga':'আমডাঙা','Sheikhdighi':'শেখদিঘি',
    'Ahiran':'আহিরণ','Chander':'চাঁদর',
    'Cooch Behar':'কোচবিহার','Asansol':'আসানসোল','Durgapur':'দুর্গাপুর','Purulia':'পুরুলিয়া',
    'Jhargram':'ঝাড়গ্রাম','Contai':'কাঁথি','Tamluk':'তমলুক','Bishnupur':'বিষ্ণুপুর',
    'Khatra':'খাতড়া','Alipurduar':'আলিপুরদুয়ার','Dinhata':'দিনহাটা','Mathabhanga':'মাথাভাঙ্গা',
    'Ghatal':'ঘাটাল','Nabadwip':'নবদ্বীপ','Arambagh':'আরামবাগ','Arambag':'আরামবাগ',
    'Manbazar':'মানবাজার','Tarkeshwar':'তারকেশ্বর','Tarakeswar':'তারকেশ্বর','Mecheda':'মেছেদা',
    'Haldia':'হলদিয়া','Baruipur':'বারুইপুর','Esplanade':'এসপ্ল্যানেড','Howrah':'হাওড়া',
    'Ranaghat':'রানাঘাট','Krishnanagar':'কৃষ্ণনগর','Malda':'মালদা','Raiganj':'রায়গঞ্জ',
    'Balurghat':'বালুরঘাট','Suri':'সিউড়ি','Sainthia':'সাঁইথিয়া','Bolpur':'বোলপুর',
    'Kalna':'কালনা','Guskara':'গুসকরা','Katwa':'কাটোয়া','Bandel':'বান্দেল',
    'Chandannagar':'চন্দননগর','Kalyani':'কল্যাণী','Barasat':'বারাসাত','Barrackpore':'ব্যারাকপুর',
    'Garia':'গড়িয়া','Berhampore':'বহরমপুর','Berhampur':'বহরমপুর','Salar':'সালার',
    'Kirnahar':'কীর্ণাহার','Karunamoyee':'করুণাময়ী','Karunamayee':'করুণাময়ী',
    'Belpahari':'বেলপাহাড়ি','Sonamukhi':'সোনামুখী','Patrasayer':'পাত্রসায়ের',
    'Onda':'ওন্দা','Mukutmanipur':'মুকুটমণিপুর','Ranibandh':'রানিবাঁধ','Simlapal':'সিমলাপাল',
    'Kharagpur (Town)':'খড়্গপুর (টাউন)','Egra':'এগরা','Ramnagar':'রামনগর','Kalinagar':'কালীনগর',
    'Kakdwip':'কাকদ্বীপ','Namkhana':'নামখানা','Falta':'ফলতা','Diamond Harbour':'ডায়মন্ড হারবার',
    'Jaynagar':'জয়নগর','Bagnan':'বাগনান','Amtala':'আমতলা','Behala':'বেহালা',
    'Nabadwip Dham':'নবদ্বীপ ধাম','Sainthia Town':'সাঁইথিয়া টাউন','Panagarh':'পানাগড়',
    'Durgapur (Station)':'দুর্গাপুর (স্টেশন)','Bishnupur (Bankura)':'বিষ্ণুপুর (বাঁকুড়া)',
    'Durgapur (City Center)':'দুর্গাপুর (সিটি সেন্টার)','Durgapur (Bus Stand)':'দুর্গাপুর (বাস স্ট্যান্ড)',
    'Durgapur (Expressway)':'দুর্গাপুর (এক্সপ্রেসওয়ে)','Bankura (Bypass)':'বাঁকুড়া (বাইপাস)',
    'Bankura (Bus Stand)':'বাঁকুড়া (বাস স্ট্যান্ড)','Bankura (Station)':'বাঁকুড়া (স্টেশন)',
    'Bankura (Pump More)':'বাঁকুড়া (পাম্প মোড়)','Bankura (More)':'বাঁকুড়া (মোড়)',
    'Bankura (Satighat Bridge)':'বাঁকুড়া (সতীঘাট ব্রিজ)','Kolkata (Karunamoyee)':'কলকাতা (করুণাময়ী)',
    'Kolkata (Esplanade)':'কলকাতা (এসপ্ল্যানেড)','Kolkata (Dharmatala)':'কলকাতা (ধর্মতলা)',
    'Kolkata (Babughat)':'কলকাতা (বাবুঘাট)',
    /* Common Kolkata-city stop/landmark names. */
    'Howrah Stn':'হাওড়া স্টেশন','Howrah Station':'হাওড়া স্টেশন','Kolkata Stn':'কলকাতা স্টেশন',
    'Kolkata Station':'কলকাতা স্টেশন','Dum Dum':'ডামডাম','Dum Dum Stn':'ডামডাম স্টেশন',
    'Nabanna':'নবান্ন','New Town':'নিউ টাউন','Airport':'এয়ারপোর্ট','Airport Gate':'এয়ারপোর্ট গেট',
    'Airport Gate-1':'এয়ারপোর্ট গেট','Airport Gate No-3':'এয়ারপোর্ট গেট',
    'Garia Depot':'গড়িয়া ডিপো','Jadavpur':'যাদবপুর','Ballygunge':'বালিগঞ্জ',
    'Ballygunge Stn':'বালিগঞ্জ স্টেশন','Gariahat':'গড়িয়াহাট','Park Street':'পার্ক স্ট্রিট',
    'Esplanade':'এসপ্ল্যানেড','Sealdah':'শিয়ালদহ','Sealdah-Rajabazar':'শিয়ালদহ-রাজাবাজার',
    'Shyambazar':'শ্যামবাজার','Dunlop':'ডানলপ','Dakshineswar':'দক্ষিণেশ্বর','Behala Chowrastha':'বেহালা চৌরাস্তা',
    'Thakurpukur':'ঠাকুরপুকুর','Joka':'জোকা','Ultadanga':'উল্টোডাঙ্গা','Bagbazar':'বাগবাজার',
    'Hazra':'হাজরা','Rashbehari Ave':'রাসবিহারী অ্যাভিনিউ','EM ByPass':'ইএম বাইপাস',
    'Science City':'সায়েন্স সিটি','Ecospace':'ইকোস্পেস','Eco Space':'ইকোস্পেস',
    'Karunamoyee':'করুণাময়ী','Sector V':'সেক্টর ফাইভ','Salt Lake':'সল্টলেক',
    'Naktala':'নাকতলা','Regent Park':'রিজেন্ট পার্ক','Ranikuthi':'রানিকুঠি',
    'Tollygunge':'টালিগঞ্জ','Park St':'পার্ক স্ট্রিট','Bbd Bag':'বিবিডি বাগ',
    'Bbd.bag':'বিবিডি বাগ','Burra Bazar':'বড়বাজার','Howrah Bridge East':'হাওড়া ব্রিজ পূর্ব',
    'Sinthi More':'সিন্থি মোড়','Chiria More':'চিড়িয়ামোড়','Paikpara':'পাইকপাড়া',
    'Central Jail':'সেন্ট্রাল জেল','Nager Bazar':'নগরবাজার','Jadavpore':'যাদবপুর',
    'Bally Khal':'বালি খাল','Malancha':'মালঞ্চ','Kolaghat':'কোলাঘাট','Chandrakona Road':'চন্দ্রকোনা রোড',
    'Chandrakona Town':'চন্দ্রকোনা টাউন','Garhbeta':'গড়বেতা','Nandigram':'নন্দীগ্রাম',
    'Jamuria':'জামুড়িয়া','Sonachura':'সোনাচুড়া','Gopiganj':'গোপীগঞ্জ','Garhbhowanipur':'গড়ভবানীপুর'
    "Barasat Chapadali":"বারাসাত চাপাড়ালি",
    "Garia Bus Stand":"গড়িয়া বাস স্ট্যান্ড",
    "Jadavpur 8B":"যাদবপুর ৮বি",
    "Tatanagar":"টাটানগর",
    "Dhanbad":"ধানবাদ",
    "Airport Terminal":"এয়ারপোর্ট টার্মিনাল",
    "Bajkul":"বাজকুল",
    "Delhi":"দিল্লি",
    "Agra":"আগ্রা",
    "Aurangabad Bihar":"ঔরঙ্গাবাদ বিহার",
    "Barhi":"বারহি",
    "Dobhi":"দোভি",
    "Etawah":"ইটাওয়া",
    "Fatehpur":"ফতেহপুর",
    "Mathura":"মথুরা",
    "Prayagraj":"প্রয়াগরাজ",
    "Sasaram":"সাসারাম",
    "Varanasi":"বারাণসী",
    "Amity University":"অ্যামিটি ইউনিভার্সিটি",
    "Parnasree":"পার্নাশ্রী",
    "Shapoorji":"শাপুরজি",
    "Raghunathpur":"রঘুনাথপুর",
    "Raniganj":"রানিগঞ্জ",
    "Solpatta":"সোলপট্টা",
    "Tajpur":"তাজপুর",
    "Tarapith":"তারাপীঠ",
    "Behala Chowrasta":"বেহালা চৌরাস্তা",
    "Deulihat":"দেউলিহাট",
    "Kolkata A.C":"কলকাতা এসি",
    "Barddhaman":"বর্ধমান",
    "Midnapur":"মেদিনীপুর",
    "Mandarmani":"মন্দারমণি",
  };

  var KEYS = Object.keys(PLACES).sort(function(a,b){ return b.length-a.length; });

  function isBn() { return d.body && d.body.classList.contains('lang-bn'); }
  function translate(s) {
    var r = String(s == null ? '' : s);
    if (!isBn()) return r;
    for (var i=0;i<KEYS.length;i++) {
      var k=KEYS[i];
      if (r.indexOf(k) > -1) r = r.split(k).join(PLACES[k]);
    }
    return r;
  }
  function translatePlace(s) {
    var raw=String(s == null ? '' : s);
    return isBn() && PLACES[raw] ? PLACES[raw] : translate(raw);
  }
  function apply(lang, emit) {
    var next = lang === 'bn' ? 'bn' : 'en';
    if (d.body) d.body.classList.toggle('lang-bn', next === 'bn');
    if (d.documentElement) d.documentElement.setAttribute('lang', next);
    var en=d.getElementById('langEn')||d.getElementById('langEN');
    var bn=d.getElementById('langBn')||d.getElementById('langBN');
    if(en){
      var enOn=next==='en';
      en.classList.toggle('on',enOn); en.classList.toggle('active',enOn); en.classList.toggle('is-active',enOn);
      en.setAttribute('aria-pressed',enOn?'true':'false');
      en.style.background=enOn?'var(--amber-soft,#f6e7c6)':'transparent';
      en.style.borderColor=enOn?'var(--amber,#b8791f)':'var(--line,#d8cfc0)';
      en.style.fontWeight=enOn?'800':'700';
    }
    if(bn){
      var bnOn=next==='bn';
      bn.classList.toggle('on',bnOn); bn.classList.toggle('active',bnOn); bn.classList.toggle('is-active',bnOn);
      bn.setAttribute('aria-pressed',bnOn?'true':'false');
      bn.style.background=bnOn?'var(--amber-soft,#f6e7c6)':'transparent';
      bn.style.borderColor=bnOn?'var(--amber,#b8791f)':'var(--line,#d8cfc0)';
      bn.style.fontWeight=bnOn?'800':'700';
    }
    try { localStorage.setItem('bj-lang',next); localStorage.setItem('seo-lang',next); } catch(e){}
    translateDom(d.body);
    if (emit) {
      try { d.dispatchEvent(new CustomEvent('bj:langchange',{detail:{lang:next}})); } catch(e){}
    }
    return next;
  }
  var ORIGINAL = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  function translateDom(root) {
    root = root || d.body;
    if (!root) return;
    var walker = d.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function(n) {
        var p=n.parentNode;
        if (!p) return NodeFilter.FILTER_REJECT;
        var tag=(p.nodeName||'').toLowerCase();
        if (tag==='script'||tag==='style'||tag==='noscript'||tag==='textarea'||tag==='input'||tag==='option') return NodeFilter.FILTER_REJECT;
        var owner=p.closest ? p.closest('.ac-drop, #stopList, [data-lang-static="en"]') : null;
        if (owner) return NodeFilter.FILTER_REJECT;
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes=[], n;
    while ((n=walker.nextNode())) nodes.push(n);
    for (var i=0;i<nodes.length;i++) {
      var node=nodes[i];
      var raw=ORIGINAL ? (ORIGINAL.has(node) ? ORIGINAL.get(node) : node.nodeValue) : node.nodeValue;
      if (ORIGINAL && !ORIGINAL.has(node)) ORIGINAL.set(node,raw);
      node.nodeValue = translate(raw);
    }
  }

  function get() {
    try {
      var v=localStorage.getItem('bj-lang')||localStorage.getItem('seo-lang');
      if(v==='bn'||v==='en') return v;
    } catch(e){}
    return ((navigator.language||'').toLowerCase().indexOf('bn')===0) ? 'bn' : 'en';
  }
  function set(lang) { return apply(lang, true); }
  function on(fn) { d.addEventListener('bj:langchange',fn); return fn; }

  w.BJLang = { places:PLACES, keys:KEYS, isBn:isBn, translate:translate, translatePlace:translatePlace, translateDom:translateDom, getLang:get, setLang:set, applyLang:apply, onChange:on };
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded',function(){ apply(get(),false); });
  else apply(get(),false);
  if (w.MutationObserver) {
    new MutationObserver(function(muts){
      for (var i=0;i<muts.length;i++) {
        for (var j=0;j<muts[i].addedNodes.length;j++) {
          var n=muts[i].addedNodes[j];
          if (n.nodeType===1) translateDom(n);
        }
      }
    }).observe(d.body || d.documentElement,{childList:true,subtree:true});
  }
})(window,document);
