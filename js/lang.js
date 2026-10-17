/* BusJatri central language system — 2026-10-05
   One source of truth for Bengali UI state and English -> Bengali place names.
   Data JSON stays English; translation is presentation-only.
*/
(function (w, d) {
  'use strict';
  if (w.BJLang) return;

  var PLACES = {
    'Adra':'আদ্রা',
    'Ahiran':'আহিরণ',
    'Airport':'এয়ারপোর্ট',
    'Airport Gate':'এয়ারপোর্ট গেট',
    'Airport Gate 1':'এয়ারপোর্ট গেট ১',
    'Airport Gate 3':'এয়ারপোর্ট গেট ৩',
    'Airport Gate No-3':'এয়ারপোর্ট গেট নং ৩',
    'Airport Gate-1':'এয়ারপোর্ট গেট',
    'Airport Terminal':'এয়ারপোর্ট টার্মিনাল',
    'Ajodhya Hills':'অযোধ্যা পাহাড়',
    'Alipurduar':'আলিপুরদুয়ার',
    'Amdanga':'আমডাঙা',
    'Amtala':'আমতলা',
    'Andal':'অন্ডাল',
    'Arambag':'আরামবাগ',
    'Arambagh':'আরামবাগ',
    'Argoal':'আরগোয়াল',
    'Arsha':'আর্শা',
    'Asansol':'আসানসোল',
    'BBD Bag':'বিবিডি বাগ',
    'Babughat':'বাবুঘাট',
    'Bagbazar':'বাগবাজার',
    'Bagdogra':'বাগডোগরা',
    'Baghmundi':'বাঘমুন্ডি',
    'Bagnan':'বাগনান',
    'Bagrakot':'বাগরাকোট',
    'Baguiati':'বাগুইআটি',
    'Baharampur':'বহরমপুর',
    'Bakshi':'বক্সি',
    'Bally':'বালি',
    'Bally Halt':'বালি হল্ট',
    'Bally Khal':'বালি খাল',
    'Ballygunge':'বালিগঞ্জ',
    'Ballygunge Station':'বালিগঞ্জ স্টেশন',
    'Ballygunge Stn':'বালিগঞ্জ স্টেশন',
    'Ballyhalt':'বালি হল্ট',
    'Balrampur':'বলরামপুর',
    'Balurghat':'বালুরঘাট',
    'Bandel':'বান্দেল',
    'Bandwan':'বান্দোয়ান',
    'Bankura':'বাঁকুড়া',
    'Bankura (Bus Stand)':'বাঁকুড়া (বাস স্ট্যান্ড)',
    'Bankura (Bypass)':'বাঁকুড়া (বাইপাস)',
    'Bankura (More)':'বাঁকুড়া (মোড়)',
    'Bankura (Pump More)':'বাঁকুড়া (পাম্প মোড়)',
    'Bankura (Satighat Bridge)':'বাঁকুড়া (সতীঘাট ব্রিজ)',
    'Bankura (Station)':'বাঁকুড়া (স্টেশন)',
    'Barabazar':'বড়বাজার',
    'Barakar':'বরাকর',
    'Barasat':'বারাসাত',
    'Barasat Chapadali':'বারাসাত চাপাড়ালি',
    'Barddhaman Alisha Bus Stand':'বর্ধমান আলিশা বাস স্ট্যান্ড',
    'Barddhaman Nawabhat Bus Stand':'বর্ধমান নবাহাট বাস স্ট্যান্ড',
    'Barddhaman Tinkonia':'বর্ধমান তিনকোণিয়া',
    'Bardhaman':'বর্ধমান',
    'Bardhaman (Alisha Bus Stand)':'বর্ধমান (আলিশা বাস স্ট্যান্ড)',
    'Bardhaman (Nawabhat Bus Stand)':'বর্ধমান (নবাহাট বাস স্ট্যান্ড)',
    'Barjora':'বড়জোড়া',
    'Barrackpore':'ব্যারাকপুর',
    'Barrackpore Court':'ব্যারাকপুর কোর্ট',
    'Baruipur':'বারুইপুর',
    'Basirhat':'বসিরহাট',
    'Batanagar':'বাটানগর',
    'Bbd Bag':'বিবিডি বাগ',
    'Bbd.bag':'বিবিডি বাগ',
    'Behala':'বেহালা',
    'Behala 14 No':'বেহালা ১৪ নম্বর',
    'Behala Chowrasta':'বেহালা চৌরাস্তা',
    'Behala Chowrastha':'বেহালা চৌরাস্তা',
    'Belda':'বেলদা',
    'Beldanga':'বেলডাঙা',
    'Belghoria':'বেলঘরিয়া',
    'Beliatore':'বেলিয়াতোড়',
    'Belpahari':'বেলপাহাড়ি',
    'Benachity':'বেনাচিটি',
    'Berhampore':'বহরমপুর',
    'Berhampur':'বহরমপুর',
    'Bhowanipore':'ভবানীপুর',
    'Binpur':'বিনপুর',
    'Bishnupur':'বিষ্ণুপুর',
    'Bishnupur (Bankura)':'বিষ্ণুপুর (বাঁকুড়া)',
    'Boga':'বোগা',
    'Bolpur':'বোলপুর',
    'Budbud':'বুদবুদ',
    'Buniadpur':'বুনিয়াদপুর',
    'Burdwan':'বর্ধমান',
    'Burdwan Tinkonia':'বর্ধমান তিনকোণিয়া',
    'Burra Bazar':'বড়বাজার',
    'Central Jail':'সেন্ট্রাল জেল',
    'Chanchal':'চাঁচল',
    'Chandannagar':'চন্দননগর',
    'Chander':'চাঁদর',
    'Chandrakona Road':'চন্দ্রকোনা রোড',
    'Chandrakona Town':'চন্দ্রকোনা টাউন',
    'Chetla':'চেতলা',
    'Chhatna':'ছাতনা',
    'Chiria More':'চিড়িয়ামোড়',
    'Chittaranjan':'চিত্তরঞ্জন',
    'Coach Behar':'কোচবিহার',
    'Contai':'কাঁথি',
    'Contai Central':'কাঁথি সেন্ট্রাল',
    'Contai Central Bus Stand':'কাঁথি সেন্ট্রাল বাস স্ট্যান্ড',
    'Cooch Behar':'কোচবিহার',
    'Coochbehar':'কোচবিহার',
    'Coronation Bridge':'করোনেশন ব্রিজ',
    'Dainhat':'দাঁইহাট',
    'Dakshineswar':'দক্ষিণেশ্বর',
    'Dalkhola':'ডালখোলা',
    'Damdim':'ডামডিম',
    'Dankuni':'ডানকুনি',
    'Dantan':'দাঁতন',
    'Darjeeling':'দার্জিলিং',
    'Debra':'দেবরা',
    'Dhamakhali':'ধামাখালি',
    'Dhanbad':'ধানবাদ',
    'Dharmatala':'ধর্মতলা',
    'Dhubulia':'ধুবুলিয়া',
    'Dhupguri':'ধূপগুড়ি',
    'Diamond':'ডায়মন্ড হারবার',
    'Diamond Harbour':'ডায়মন্ড হারবার',
    'Digha':'দীঘা',
    'Dinhata':'দিনহাটা',
    'Dum Dum':'ডামডাম',
    'Dum Dum Stn':'ডামডাম স্টেশন',
    'Dumdum':'ডামডাম',
    'Dunlop':'ডানলপ',
    'Durgachak':'দূর্গাচক',
    'Durgachak Central Bus Stand':'দূর্গাচক সেন্ট্রাল বাস স্ট্যান্ড',
    'Durgapur':'দুর্গাপুর',
    'Durgapur (Bus Stand)':'দুর্গাপুর (বাস স্ট্যান্ড)',
    'Durgapur (City Center)':'দুর্গাপুর (সিটি সেন্টার)',
    'Durgapur (Expressway)':'দুর্গাপুর (এক্সপ্রেসওয়ে)',
    'Durgapur (Station)':'দুর্গাপুর (স্টেশন)',
    'Durgapur City Centre':'দুর্গাপুর সিটি সেন্টার',
    'Durgapur Station':'দুর্গাপুর স্টেশন',
    'EM ByPass':'ইএম বাইপাস',
    'Eco Space':'ইকোস্পেস',
    'Eco space':'ইকোস্পেস',
    'Ecospace':'ইকোস্পেস',
    'Egra':'এগরা',
    'Esplanade':'এসপ্ল্যানেড',
    'Falakata':'ফালাকাটা',
    'Falta':'ফলতা',
    'Farakka':'ফারাক্কা',
    'Fatapukur':'ফাটাপুকুর',
    'Fulbari':'ফুলবাড়ি',
    'Fulkusma':'ফুলকুসমা',
    'Gangarampur':'গঙ্গারামপুর',
    'Garhbeta':'গড়বেতা',
    'Garhbhowanipur':'গড়ভবানীপুর',
    'Garia':'গড়িয়া',
    'Garia Bus Stand':'গড়িয়া বাস স্ট্যান্ড',
    'Garia Depot':'গড়িয়া ডিপো',
    'Gariahat':'গড়িয়াহাট',
    'Gazole':'গাজোল',
    'Ghatal':'ঘাটাল',
    'Gopiballabpur':'গোপীবল্লভপুর',
    'Gopiganj':'গোপীগঞ্জ',
    'Guskara':'গুসকরা',
    'Habra':'হাবড়া',
    'Habra Depot':'হাবড়া ডিপো',
    'Habra Station':'হাবড়া স্টেশন',
    'Haldia':'হলদিয়া',
    'Haldia Township':'হলদিয়া টাউনশিপ',
    'Hazra':'হাজরা',
    'Howrah':'হাওড়া',
    'Howrah Bridge East':'হাওড়া ব্রিজ পূর্ব',
    'Howrah Maidan':'হাওড়া ময়দান',
    'Howrah Station':'হাওড়া স্টেশন',
    'Howrah Stn':'হাওড়া স্টেশন',
    'Ilam Bazar':'ইলাম বাজার',
    'Ilambazar':'ইলাম বাজার',
    'Islampur':'ইসলামপুর',
    'Itahar':'ইটাহার',
    'Jadavpore':'যাদবপুর',
    'Jadavpur':'যাদবপুর',
    'Jadavpur 8B':'যাদবপুর ৮বি',
    'Jalpaiguri':'জলপাইগুড়ি',
    'Jalpaiguri Bypass':'জলপাইগুড়ি বাইপাস',
    'Jamuria':'জামুড়িয়া',
    'Jangipur':'জঙ্গীপুর',
    'Jaynagar':'জয়নগর',
    'Jhargram':'ঝাড়গ্রাম',
    'Joka':'জোকা',
    'Joka Tram Depot':'জোকা ট্রাম ডিপো',
    'Kabilepur':'কবিলেপুর',
    'Kaijuri Bazar':'কৈজুরী বাজার',
    'Kakdwip':'কাকদ্বীপ',
    'Kaliachak':'কালিয়াচক',
    'Kalimpong':'কালিম্পং',
    'Kalinagar':'কালীনগর',
    'Kalna':'কালনা',
    'Kalyani':'কল্যাণী',
    'Kandi':'কান্দি',
    'Kandra':'কান্দ্রা',
    'Kanthi':'কাঁথি',
    'Karimpur':'করিমপুর',
    'Karunamayee':'করুণাময়ী',
    'Karunamoyee':'করুণাময়ী',
    'Katwa':'কাটোয়া',
    'Kharagpur':'খড়্গপুর',
    'Kharagpur (Town)':'খড়্গপুর (টাউন)',
    'Kharagpur Station':'খড়্গপুর স্টেশন',
    'Khatra':'খাতড়া',
    'Kirnahar':'কীর্ণাহার',
    'Kishanganj':'কিশনগঞ্জ',
    'Koch Bihar':'কোচবিহার',
    'Kolaghat':'কোলাঘাট',
    'Kolkata':'কলকাতা',
    'Kolkata (Babughat)':'কলকাতা (বাবুঘাট)',
    'Kolkata (Dharmatala)':'কলকাতা (ধর্মতলা)',
    'Kolkata (Esplanade)':'কলকাতা (এসপ্ল্যানেড)',
    'Kolkata (Karunamoyee)':'কলকাতা (করুণাময়ী)',
    'Kolkata (Santragachi)':'কলকাতা (সাঁতরাগাছি)',
    'Kolkata Station':'কলকাতা স্টেশন',
    'Kolkata Stn':'কলকাতা স্টেশন',
    'Krishnanagar':'কৃষ্ণনগর',
    'Kurseong':'কার্শিয়াং',
    'Lalgola':'লালগোলা',
    'Madhyamgram':'মধ্যমগ্রাম',
    'Mainaguri':'ময়নাগুড়ি',
    'Malancha':'মালঞ্চ',
    'Malbazar':'মালবাজার',
    'Malda':'মালদা',
    'Manbazar':'মানবাজার',
    'Mathabhanga':'মাথাভাঙ্গা',
    'Mecheda':'মেছেদা',
    'Medinipur':'মেদিনীপুর',
    'Memari':'মেমারি',
    'Midnapore':'মেদিনীপুর',
    'Midnapur':'মেদিনীপুর',
    'Midnapur Central Bus Stand':'মেদিনীপুর সেন্ট্রাল বাস স্ট্যান্ড',
    'Milk Colony':'মিল্ক কলোনি',
    'Mohar':'মোহর',
    'Moynaguri':'ময়নাগুড়ি',
    'Mukutmanipur':'মুকুটমণিপুর',
    'Nabadwip':'নবদ্বীপ',
    'Nabadwip Dham':'নবদ্বীপ ধাম',
    'Nabanna':'নবান্ন',
    'Nager Bazar':'নগরবাজার',
    'Naihati':'নৈহাটি',
    'Naktala':'নাকতলা',
    'Namkhana':'নামখানা',
    'Nandigram':'নন্দীগ্রাম',
    'Napara':'নাপাড়া',
    'New Town':'নিউ টাউন',
    'Newtown':'নিউটাউন',
    'Odlabari':'ওদলাবাড়ি',
    'Onda':'ওন্দা',
    'Oodlabari':'ওদলাবাড়ি',
    'Paikpara':'পাইকপাড়া',
    'Panagarh':'পানাগড়',
    'Panitanki':'পানিট্যাঙ্কি',
    'Park St':'পার্ক স্ট্রিট',
    'Park Street':'পার্ক স্ট্রিট',
    'Patrasayer':'পাত্রসায়ের',
    'Phulia':'ফুলিয়া',
    'Purulia':'পুরুলিয়া',
    'Raiganj':'রায়গঞ্জ',
    'Raipur':'রাইপুর',
    'Rajabazar':'রাজাবাজার',
    'Rajarhat':'রাজারহাট',
    'Ramganj':'রামগঞ্জ',
    'Ramnagar':'রামনগর',
    'Rampurhat':'রামপুরহাট',
    'Ranaghat':'রানাঘাট',
    'Ranibandh':'রানিবাঁধ',
    'Ranikuthi':'রানিকুঠি',
    'Rashbehari Ave':'রাসবিহারী অ্যাভিনিউ',
    'Regent Park':'রিজেন্ট পার্ক',
    'Rishra':'রিষড়া',
    'Sahararhat':'সাহারারহাট',
    'Sainthia':'সাঁইথিয়া',
    'Sainthia Town':'সাঁইথিয়া টাউন',
    'Salar':'সালার',
    'Salt Lake':'সল্টলেক',
    'Saltlake':'সল্টলেক',
    'Saltlake Karunamoyee':'সল্টলেক করুণাময়ী',
    'Salugara':'সালুগাড়া',
    'Samsi':'সামসি',
    'Santragachi':'সাঁতরাগাছি',
    'Science City':'সায়েন্স সিটি',
    'Sealdah':'শিয়ালদহ',
    'Sealdah-Rajabazar':'শিয়ালদহ-রাজাবাজার',
    'Sector V':'সেক্টর ফাইভ',
    'Serampore':'শ্রীরামপুর',
    'Sevoke':'সেবক',
    'Shantipur':'শান্তিপুর',
    'Shapoorji':'শাপুরজি',
    'Sheikhdighi':'শেখদিঘি',
    'Shyambazar':'শ্যামবাজার',
    'Silda':'শিলদা',
    'Siliguri':'শিলিগুড়ি',
    'Simlapal':'সিমলাপাল',
    'Sinthi More':'সিন্থি মোড়',
    'Sitai':'সিতাই',
    'Sonachura':'সোনাচুড়া',
    'Sonamukhi':'সোনামুখী',
    'Sujapur':'সুজাপুর',
    'Suri':'সিউড়ি',
    'Tamluk':'তমলুক',
    'Tapan':'তপন',
    'Tarakeshwar':'তারকেশ্বর',
    'Tarakeswar':'তারকেশ্বর',
    'Tarapith':'তারাপীঠ',
    'Taratala':'তারাতলা',
    'Tarkeshwar':'তারকেশ্বর',
    'Tatanagar':'টাটানগর',
    'Thakurpukur':'ঠাকুরপুকুর',
    'Tollygunge':'টালিগঞ্জ',
    'Tollygunge Metro':'টালিগঞ্জ মেট্রো',
    'Ultadanga':'উল্টোডাঙ্গা'
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
