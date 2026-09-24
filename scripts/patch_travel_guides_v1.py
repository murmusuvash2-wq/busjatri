# Travel guides batch 1 (manual, replaces deleted cron): 6 stands.
# Durgapur, Siliguri, Asansol, Howrah Station, Bardhaman, Barasat.
# Adds entries to GUIDES + GUIDES_BN in scripts/gen_stand_v2.py.
# All bus names/times mined from data/busjatri_data.json - nothing fabricated.
# Idempotent + backslash-free.

import io

P = 'scripts/gen_stand_v2.py'
MARK = 'troika-park-dgp'

EN_BLOCK = '''
    "durgapur": {
        "intro": ("Around Durgapur", "দুর্গাপুরের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Durgapur station on the Howrah–Delhi main line · 🛣️ <b>Road:</b> NH-19 to Asansol–Dhanbad, SH to Bankura · listed buses: Kolkata 20, Nabadwip 9, Kalna 3.",
        "cards": [
            {"icon": "🌊", "name": "Durgapur Barrage", "bn": "দুর্গাপুর ব্যারাজ",
             "desc": "Damodar river barrage with a long tree-lined top road — the town's evening walk",
             "bus": "🚶 Short local ride from the stand — shared autos run all day",
             "maps": "Durgapur+Barrage",
             "why": "river view, sunset walk, 1950s DVC engineering",
             "when": "October–March, evening",
             "stay": None, "stay_extra": "Day trip in Durgapur — {LINK}",
             "stay_link": "hotels+in+Durgapur", "stay_text": "stay in town"},
            {"icon": "🎡", "name": "Troika Park", "bn": "ট্রোইকা পার্ক",
             "desc": "City amusement park by the lake at City Centre — rides and open lawns",
             "bus": "🚶 Walk or short auto from the City Centre stands",
             "maps": "Troika+Park+Durgapur",
             "why": "family rides, lakeside path, street food outside",
             "when": "October–February, afternoon",
             "stay": None, "stay_extra": "Day trip in Durgapur — {LINK}",
             "stay_link": "hotels+in+Durgapur", "stay_text": "stay in town"},
        ],
    },
    "siliguri": {
        "intro": ("Around Siliguri", "শিলিগুড়ির আশপাশ"),
        "note": "🚉 <b>Rail:</b> NJP junction and Siliguri Town station · ✈️ <b>Air:</b> Bagdogra airport 12 km · 🛣️ <b>Road:</b> the gate to Darjeeling, Kalimpong, Sikkim and the Dooars.",
        "cards": [
            {"icon": "⛰️", "name": "Darjeeling", "bn": "দার্জিলিং",
             "desc": "Queen of the hills — toy train, Tiger Hill and tea gardens",
             "bus": "🚌 <b>NBSTC</b> 6:00, 6:30, 7:00, 7:30, 8:30 & 10:30 AM — direct from this stand",
             "maps": "Darjeeling",
             "why": "Tiger Hill sunrise, UNESCO toy train, mall road",
             "when": "March–May & October–December, start early morning",
             "stay": "hotels+in+Darjeeling"},
            {"icon": "🏞️", "name": "Mirik", "bn": "মিরিক",
             "desc": "Lake town wrapped in tea gardens, an hour and a half away",
             "bus": "🚌 <b>NBSTC Siliguri–Mirik</b> 7:00 AM · 11:30 AM · 3:30 PM — direct",
             "maps": "Mirik+lake",
             "why": "Sumendu lake boating, orange orchards, tea estate views",
             "when": "October–April",
             "stay": "hotels+in+Mirik"},
            {"icon": "🏔️", "name": "Kalimpong", "bn": "কালিম্পং",
             "desc": "Hill town above the Teesta — monasteries and valley views",
             "bus": "🚌 <b>NBSTC Siliguri–Kalimpong</b> 6:30, 7:15, 8:45, 10:30, 11:40 AM & 1:15 PM — direct",
             "maps": "Kalimpong",
             "why": "Durpin monastery, Teesta views, flower nurseries",
             "when": "March–May & October–December",
             "stay": "hotels+in+Kalimpong"},
            {"icon": "🌸", "name": "Gangtok (Sikkim)", "bn": "গংটক",
             "desc": "Capital of Sikkim — MG Marg, monasteries and Himalayan views",
             "bus": "🚌 <b>NBSTC Siliguri–Gangtok</b> 5:30 AM & 8:15 AM — direct",
             "maps": "Gangtok",
             "why": "MG Marg walk, Rumtek monastery, hill viewpoints",
             "when": "March–June & October–December; carry photo ID for Sikkim entry",
             "stay": "hotels+in+Gangtok"},
        ],
    },
    "asansol": {
        "intro": ("Around Asansol", "আসানসোলের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Asansol Junction on the Howrah–Delhi main line · 🛣️ <b>Road:</b> NH-19 to Dhanbad, NH-60 to Bankura · 19 listed buses to Kolkata.",
        "cards": [
            {"icon": "🌊", "name": "Maithon Dam", "bn": "মাইথন বাঁধ",
             "desc": "Damodar valley dam and lake — boating and viewpoints",
             "bus": "🚌 <b>Shyamoli Paribahan</b> Dhanbad-route buses (2 daily) pass the Maithon dam road",
             "maps": "Maithon+Dam",
             "why": "lake boating, deer park, dam viewpoint",
             "when": "October–March, morning",
             "stay": "hotels+near+Maithon"},
            {"icon": "🛕", "name": "Kalyaneswari Temple", "bn": "কল্যাণেশ্বরী মন্দির",
             "desc": "Old Kali temple on the Damodar, just before the dam",
             "bus": "🚌 Same Maithon-route buses — get off at Kalyaneswari, before the dam",
             "maps": "Kalyaneswari+Temple",
             "why": "ancient temple by the river, quiet ghat",
             "when": "Year-round, mornings",
             "stay": None, "stay_extra": "Day trip from Asansol — {LINK}",
             "stay_link": "hotels+in+Asansol", "stay_text": "stay in town"},
            {"icon": "⛰️", "name": "Biharinath Hill", "bn": "বিহারীনাথ পাহাড়",
             "desc": "The highest hill of the area — old Shiva temple and forest trails",
             "bus": "🚌 No direct listed bus — take an NH-60 Bankura-side local toward Saltora and ask for Biharinath, or hire a car",
             "maps": "Biharinath+Hill",
             "why": "hill climb, Biharinath Shiva temple, sunrise views",
             "when": "October–February, start early",
             "stay": None, "stay_extra": "Day trip from Asansol — {LINK}",
             "stay_link": "hotels+in+Asansol", "stay_text": "stay in town"},
        ],
    },
    "howrah-station": {
        "intro": ("Around Howrah Station", "হাওড়া স্টেশনের আশপাশ"),
        "note": "🚉 <b>Rail:</b> one of India's biggest stations — every Howrah line starts here · 🛣️ <b>Road:</b> 133 listed buses across 100+ routes.",
        "cards": [
            {"icon": "🌉", "name": "Howrah Bridge & Mullick Ghat", "bn": "হাওড়া ব্রিজ ও মল্লিক ঘাট",
             "desc": "Walk the iconic bridge at sunrise; the flower market roars below",
             "bus": "🚶 Walk out of the station — the bridge is right there",
             "maps": "Howrah+Bridge+Mullick+Ghat+flower+market",
             "why": "Rabindra Setu walk, Mullick Ghat flower market, river views",
             "when": "Year-round, sunrise for the flower market",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah", "stay_text": "stay in the city"},
            {"icon": "🦩", "name": "Santragachi Jheel", "bn": "সাঁতরাগাছি জিল",
             "desc": "Big lake beside the rail station — winter migratory birds",
             "bus": "🚉 Two stations down the Howrah–Kharagpur line (10 min), then a short walk",
             "maps": "Santragachi+Jheel+lake",
             "why": "winter waterbirds, lakeside walk, photography",
             "when": "November–February, early morning",
             "stay": None, "stay_extra": "Day trip in the city — {LINK}",
             "stay_link": "hotels+in+Howrah", "stay_text": "stay in the city"},
            {"icon": "🌅", "name": "Gadiara", "bn": "গড়িয়ারা",
             "desc": "River confluence — the Damodar meets the Rupnarayan and the Hooghly",
             "bus": "🚉 Train toward Mecheda, then a short local ride (no direct listed bus from this stand — ask at the stand)",
             "maps": "Gadiara+Howrah",
             "why": "riverside sunset, boat rides, weekend crowds",
             "when": "October–March",
             "stay": "hotels+in+Gadiara"},
        ],
    },
    "bardhaman": {
        "intro": ("Around Bardhaman", "বর্ধমানের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Bardhaman Junction — Howrah main line and Katwa line meet here · 🛣️ <b>Road:</b> GT Road (NH-19) to Durgapur · 26 listed buses to Kolkata.",
        "cards": [
            {"icon": "🏰", "name": "Bardhaman Rajbari", "bn": "বর্ধমান রাজবাড়ি",
             "desc": "Palace of the Maharajas of Burdwan — gateway, tanks and old temples around",
             "bus": "🚶 Short auto-rickshaw ride from the stand",
             "maps": "Bardhaman+Rajbari+palace",
             "why": "royal gateway, Sarbamangala temple nearby, old town walk",
             "when": "October–March, morning",
             "stay": "hotels+in+Bardhaman"},
            {"icon": "🛕", "name": "108 Shiva Temples", "bn": "১০৮ শিবমন্দির",
             "desc": "Two rows of 108 Shiva shrines built by the Burdwan royal family at Nababhat",
             "bus": "🚶 Local auto from the stand (Nababhat area)",
             "maps": "108+Shiva+Temples+Bardhaman+Nababhat",
             "why": "unique double-arc temple courtyard, quiet and photogenic",
             "when": "Year-round, Shivaratri is the big day",
             "stay": None, "stay_extra": "Day trip from Bardhaman — {LINK}",
             "stay_link": "hotels+in+Bardhaman", "stay_text": "stay in town"},
            {"icon": "🏛️", "name": "Kalna Temples", "bn": "কালনার মন্দির",
             "desc": "Temple town 30 km away — Pratapeswar Deul and the 108 Shiva temples of Kalna",
             "bus": "🚉 Frequent Katwa-line locals from Bardhaman Junction (about 30 min) — buses via the Katwa road also run, ask at the stand",
             "maps": "Kalna+terracotta+temples",
             "why": "terracotta Deul, 108-temple complex, riverside town",
             "when": "October–March",
             "stay": "hotels+in+Kalna"},
        ],
    },
    "barasat": {
        "intro": ("Around Barasat", "বারাসাতের আশপাশ"),
        "note": "🚉 <b>Rail:</b> Barasat on the Sealdah–Bongaon line · 🛣️ <b>Road:</b> Jessore Road runs to the Bangladesh border · 10 listed buses to Digha.",
        "cards": [
            {"icon": "🌳", "name": "Mangal Pandey Park", "bn": "মঙ্গল পাণ্ডে উদ্যান",
             "desc": "1857 memorial park on the Hooghly at Barrackpore",
             "bus": "🚌 <b>DS-34</b> · <b>C-29</b> — direct to Barrackpore Court",
             "maps": "Mangal+Pandey+Park+Barrackpore",
             "why": "riverfront park, 1857 history, ferry ghat",
             "when": "October–March, morning",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
            {"icon": "🌊", "name": "Ichhamati River, Bagdah", "bn": "ইছামতী নদী, বাগদা",
             "desc": "Quiet riverside on the Bangladesh border — boats and open fields",
             "bus": "🚌 <b>D7</b> runs to Bagdah from this stand",
             "maps": "Ichhamati+river+Bagdah",
             "why": "river bank, country boats, border village life",
             "when": "October–March",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
            {"icon": "⛴️", "name": "Hemnagar", "bn": "হেমনগর",
             "desc": "Riverside town on the Ichhamati — ghats and a lively weekly haat",
             "bus": "🚌 <b>D-34</b> runs to Hemnagar from this stand",
             "maps": "Hemnagar+North+24+Parganas",
             "why": "river ghats, border-area haat, boat rides",
             "when": "October–March, haat days",
             "stay": None, "stay_extra": "Day trip from Barasat — {LINK}",
             "stay_link": "hotels+in+Barasat", "stay_text": "stay in town"},
        ],
    },
'''

BN_BLOCK = '''
    "durgapur": {
        "note": "🚉 <b>রেল:</b> হাওড়া–দিল্লি প্রধান লাইনের দুর্গাপুর স্টেশন · 🛣️ <b>রাস্তা:</b> আসানসল–ধানবাদ এনএইচ-১৯, বাঁকুড়া এসএইচ · তালিকাভুক্ত বাস: কলকাতা ২০টি, নবদ্বীপ ৯টি, কালনা ৩টি।",
        "cards": [
            {"desc_bn": "দামোদর নদীর ওপর ব্যারাজ — ওপরে গাছে ঢাকা লম্বা রাস্তা, শহরের সন্ধ্যার হাঁটার জায়গা",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অল্প লোকাল রাইড — শেয়ারড অটো সারাদিন পাওয়া যায়",
             "why_bn": "নদীর দৃশ্য, সূর্যাস্তে হাঁটা, পঞ্চাশের দশকের ডিভিসি বাঁধ",
             "when_bn": "অক্টোবর–মার্চ, সন্ধ্যায়",
             "stay_extra_bn": "দুর্গাপুরে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "সিটি সেন্টারে হ্রদের ধারে বিনোদন পার্ক — রাইড, খোলা লন",
             "bus_bn": "🚶 সিটি সেন্টার স্ট্যান্ড থেকে হাঁটা দূরত্ব বা অটো",
             "why_bn": "পরিবারের সঙ্গে রাইড, হ্রদের ধারে পথ, বাইরে স্ট্রিট ফুড",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, বিকেলে",
             "stay_extra_bn": "দুর্গাপুরে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "siliguri": {
        "note": "🚉 <b>রেল:</b> এনজেপি জংশন ও শিলিগুড়ি টাউন স্টেশন · ✈️ <b>বিমান:</b> বাগডোগরা, ১২ কিমি · 🛣️ <b>রাস্তা:</b> দার্জিলিং, কালিম্পং, সিকিম ও ডুয়ার্সের পথ এখান থেকেই।",
        "cards": [
            {"desc_bn": "পাহাড়ের রানি — টয় ট্রেন, টাইগার হিল আর চা-বাগান",
             "bus_bn": "🚌 <b>NBSTC</b> 6:00, 6:30, 7:00, 7:30, 8:30 & 10:30 AM — এই স্ট্যান্ড থেকে সরাসরি",
             "why_bn": "টাইগার হিলের সূর্যোদয়, ইউনেস্কো টয় ট্রেন, মল রোড",
             "when_bn": "মার্চ–মে ও অক্টোবর–ডিসেম্বর, ভোরে রওনা দিন"},
            {"desc_bn": "চা-বাগানে ঘেরা হ্রদের শহর, দেড় ঘণ্টার পথ",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–মিরিক</b> 7:00 AM · 11:30 AM · 3:30 PM — সরাসরি",
             "why_bn": "সুমেন্দু হ্রদে বোটিং, কমলালেবু বাগান, চা-বাগানের দৃশ্য",
             "when_bn": "অক্টোবর–এপ্রিল"},
            {"desc_bn": "তিস্তার ওপরে পাহাড়ের শহর — মঠ আর উপত্যকার দৃশ্য",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–কালিম্পং</b> 6:30, 7:15, 8:45, 10:30, 11:40 AM & 1:15 PM — সরাসরি",
             "why_bn": "দুরপিন মঠ, তিস্তার দৃশ্য, ফুলের নার্সারি",
             "when_bn": "মার্চ–মে ও অক্টোবর–ডিসেম্বর"},
            {"desc_bn": "সিকিমের রাজধানী — এম জি মার্গ, মঠ আর হিমালয়ের দৃশ্য",
             "bus_bn": "🚌 <b>NBSTC শিলিগুড়ি–গংটক</b> 5:30 AM & 8:15 AM — সরাসরি",
             "why_bn": "এম জি মার্গ, রুমটেক মঠ, পাহাড়ের ভিউ পয়েন্ট",
             "when_bn": "মার্চ–জুন ও অক্টোবর–ডিসেম্বর; সিকিমে ঢোকার জন্য ছবির আই-কার্ড নিন"},
        ],
    },
    "asansol": {
        "note": "🚉 <b>রেল:</b> হাওড়া–দিল্লি প্রধান লাইনের আসানসল জংশন · 🛣️ <b>রাস্তা:</b> ধানবাদ এনএইচ-১৯, বাঁকুড়া এনএইচ-৬০ · কলকাতায় ১৯টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "দামোদর উপত্যকার বাঁধ আর হ্রদ — বোটিং ও ভিউ পয়েন্ট",
             "bus_bn": "🚌 <b>Shyamoli Paribahan</b> ধানবাদ রুটের বাস (দিনে ২টি) মাইথন বাঁধের রাস্তা ছোঁয়",
             "why_bn": "হ্রদে বোটিং, হরিণ পার্ক, বাঁধের ভিউ পয়েন্ট",
             "when_bn": "অক্টোবর–মার্চ, সকালে"},
            {"desc_bn": "দামোদরের ধারে পুরোনো কালীমন্দির, বাঁধের আগে",
             "bus_bn": "🚌 মাইথন রুটের একই বাস — বাঁধের আগে কল্যাণেশ্বরীতে নেমে যান",
             "why_bn": "নদীর ধারে প্রাচীন মন্দির, শান্ত ঘাট",
             "when_bn": "সারা বছর, সকালে",
             "stay_extra_bn": "আসানসল থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "এলাকার সবচেয়ে উঁচু পাহাড় — পুরোনো শিবমন্দির আর জঙ্গলের পথ",
             "bus_bn": "🚌 সরাসরি তালিকাভুক্ত বাস নেই — এনএইচ-৬০ বাঁকুড়া দিকের লোকাল বাস ধরে শালতোড়ার দিকে যান, বিহারীনাথ জিজে নিন; চাইলে গাড়ি ভাড়া করুন",
             "why_bn": "পাহাড় বোয়ানো, বিহারীনাথ শিবমন্দির, সূর্যোদয়ের দৃশ্য",
             "when_bn": "অক্টোবর–ফেব্রুয়ারি, ভোরে রওনা দিন",
             "stay_extra_bn": "আসানসল থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
    "howrah-station": {
        "note": "🚉 <b>রেল:</b> দেশের অন্যতম বড় স্টেশন — হাওড়ার সব লাইন এখান থেকে ছাড়ে · 🛣️ <b>রাস্তা:</b> ১০০-র বেশি রুটে ১৩৩টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "ভোরে সেতু পেরিয়ে হাঁটুন; নিচে মল্লিক ঘাটের ফুলের বাজার",
             "bus_bn": "🚶 স্টেশন থেকে বেরোলেই সেতু",
             "why_bn": "রবীন্দ্র সেতুতে হাঁটা, মল্লিক ঘাটের ফুলের বাজার, নদীর দৃশ্য",
             "when_bn": "সারা বছর, ফুলের বাজারের জন্য ভোরে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "স্টেশনের পাশে বড় হ্রদ — শীতে পরিযায়ী পাখি",
             "bus_bn": "🚉 হাওড়া–খড়্গপুর লাইনে দু'স্টেশন (১০ মিনিট), তারপর অল্প হাঁটা",
             "why_bn": "শীতের জলপাখি, হ্রদের ধারে হাঁটা, ছবি তোলা",
             "when_bn": "নভেম্বর–ফেব্রুয়ারি, ভোরে",
             "stay_extra_bn": "শহরের মধ্যেই দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "নদীর সঙ্গমস্থল — দামোদর রূপনারায়ণ ও হুগলির সাথে মেশে",
             "bus_bn": "🚉 মেচেদা এগিয়ে ট্রেন, তারপর অল্প লোকাল রাইড (এই স্ট্যান্ড থেকে সরাসরি তালিকাভুক্ত বাস নেই — জেনে নিন)",
             "why_bn": "নদীর ধারে সূর্যাস্ত, নৌকা ভ্রমণ, ছুটির দিনের ভিড়",
             "when_bn": "অক্টোবর–মার্চ"},
        ],
    },
    "bardhaman": {
        "note": "🚉 <b>রেল:</b> বর্ধমান জংশন — হাওড়া মেন ও কাটোয়া লাইনের মিলনস্থল · 🛣️ <b>রাস্তা:</b> দুর্গাপুর অভিমুখে জিটি রোড (এনএইচ-১৯) · কলকাতায় ২৬টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "বর্ধমানের মহারাজাদের রাজবাড়ি — ফটক, দিঘি আর চারপাশে পুরোনো মন্দির",
             "bus_bn": "🚶 স্ট্যান্ড থেকে অটো-রিকশায় অল্প পথ",
             "why_bn": "রাজকীয় ফটক, কাছেই সর্বমঙ্গলা মন্দির, পুরোনো শহরে হাঁটা",
             "when_bn": "অক্টোবর–মার্চ, সকালে"},
            {"desc_bn": "নবাবহাটে বর্ধমান রাজপরিবারের তৈরি দু'সারি ১০৮টি শিবমন্দির",
             "bus_bn": "🚶 স্ট্যান্ড থেকে লোকাল অটো (নবাবহাট এলাকা)",
             "why_bn": "অনন্য দু'সারি মন্দিরের উঠান, শান্ত ও ছবির মতো",
             "when_bn": "সারা বছর, শিবরাত্রিতে বিশেষ আয়োজন",
             "stay_extra_bn": "বর্ধমান থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "৩০ কিমি দূরে মন্দিরের শহর কালনা — প্রতাপেশ্বর দেউল আর ১০৮ শিবমন্দির",
             "bus_bn": "🚉 বর্ধমান জংশন থেকে কাটোয়া লাইনের লোকাল (প্রায় ৩০ মিনিট) — কাটোয়া রোডের বাসও চলে, জেনে নিন",
             "why_bn": "পোড়ামাটির দেউল, ১০৮ মন্দিরের কমপ্লেক্স, নদীর ধারে শহর",
             "when_bn": "অক্টোবর–মার্চ"},
        ],
    },
    "barasat": {
        "note": "🚉 <b>রেল:</b> শিয়ালদহ–বনগাঁ লাইনে বারাসাত · 🛣️ <b>রাস্তা:</b> যশোর রোড বাংলাদেশ সীমান্ত পর্যন্ত · দীঘায় ১০টি তালিকাভুক্ত বাস।",
        "cards": [
            {"desc_bn": "ব্যারাকপুরে হুগলির ধারে ১৮৫৭-র স্মৃতিতে উদ্যান",
             "bus_bn": "🚌 <b>DS-34</b> · <b>C-29</b> — ব্যারাকপুর কোর্ট পর্যন্ত সরাসরি",
             "why_bn": "নদীর ধারে পার্ক, ১৮৫৭-র ইতিহাস, ফেরি ঘাট",
             "when_bn": "অক্টোবর–মার্চ, সকালে",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "বাংলাদেশ সীমান্তে ইছামতীর শান্ত পাড় — নৌকা আর খোলা মাঠ",
             "bus_bn": "🚌 <b>D7</b> এই স্ট্যান্ড থেকে বাগদা পর্যন্ত চলে",
             "why_bn": "নদীর পাড়, দেশি নৌকা, সীমান্ত গ্রামের জীবন",
             "when_bn": "অক্টোবর–মার্চ",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
            {"desc_bn": "ইছামতীর ধারে শহর — ঘাট আর সাপ্তাহিক হাট",
             "bus_bn": "🚌 <b>D-34</b> এই স্ট্যান্ড থেকে হেমনগর পর্যন্ত চলে",
             "why_bn": "নদীর ঘাট, সীমান্ত এলাকার হাট, নৌকা ভ্রমণ",
             "when_bn": "অক্টোবর–মার্চ, হাটের দিনে",
             "stay_extra_bn": "বারাসাত থেকে দিনের ভ্রমণ — {LINK}",
             "stay_text_bn": "শহরে থাকুন"},
        ],
    },
'''


def main():
    s = io.open(P, encoding='utf-8').read()

    if MARK in s:
        print('already patched')
        return

    # --- insert into GUIDES (just before its closing brace) ---
    a1 = chr(10) + chr(10) + chr(10) + chr(10) + 'GUIDES_BN = {'
    if a1 not in s:
        print('ANCHOR 1 NOT FOUND')
        raise SystemExit(1)
    i = s.find(a1)
    # GUIDES' closing brace is the last '}' before the blank lines
    k = s.rfind('}', 0, i)
    s = s[:k] + EN_BLOCK + s[k:]

    # --- insert into GUIDES_BN (just before its closing brace) ---
    a2 = chr(10) + chr(10) + 'def _merge_guide_bn():'
    if a2 not in s:
        print('ANCHOR 2 NOT FOUND')
        raise SystemExit(1)
    j = s.find(a2)
    k2 = s.rfind('}', 0, j)
    s = s[:k2] + BN_BLOCK + s[k2:]

    io.open(P, 'w', encoding='utf-8').write(s)
    print('guides inserted: 6 stands (EN + BN)')


if __name__ == '__main__':
    main()
