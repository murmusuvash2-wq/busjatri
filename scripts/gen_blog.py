#!/usr/bin/env python3
"""BusJatri Bengali blog: static article pages + index + homepage link + sitemap.

Articles are embedded in this script so the whole blog regenerates
idempotently on every run (part of the fb-update rebuild chain).
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://busjatri.in"
TODAY = date.today().isoformat()

GA4 = (
    '<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"></script>\n'
    "<script>\n"
    "  window.dataLayer = window.dataLayer || [];\n"
    "  function gtag(){dataLayer.push(arguments);}\n"
    "  gtag('js', new Date());\n"
    "  gtag('config', 'G-L4E3D1YX9X');\n"
    "</script>\n"
)

HEADER = """<header class="header">
  <div class="container header-inner">
    <a href="../index.html" class="logo" style="text-decoration:none;color:inherit">
      <svg class="icon" viewBox="0 0 24 24" style="width:1.35rem;height:1.35rem;color:var(--amber)" aria-hidden="true">
        <path d="M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"/><path d="M4 16h16"/>
      </svg>
      Bus<span>Jatri</span>
    </a>
    <nav style="display:flex;gap:10px;align-items:center;font-size:13px">
      <a href="../index.html" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Home</a>
      <a href="../bus-time-table/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Routes</a>
      <a href="../via/" style="color:var(--ink-dim);text-decoration:none;font-weight:600">Stops</a>
      <button id="bjThemeBtn" aria-label="Toggle dark mode" style="background:var(--surface,#fffcf4);border:1px solid var(--line,#ccc);border-radius:999px;padding:6px 12px;cursor:pointer;font-weight:600;color:var(--ink-dim,#665);font-size:13px;font-family:inherit;line-height:1.2">◐</button>
    </nav>
  </div>
</header>
<script>(function(){try{var b=document.getElementById("bjThemeBtn");if(!b)return;if(localStorage.getItem("seo-theme")==="dark"){document.body.classList.add("dark");b.textContent="\u2600";}b.addEventListener("click",function(){var d=document.body.classList.toggle("dark");try{localStorage.setItem("seo-theme",d?"dark":"light");}catch(e){}b.textContent=d?"\u2600":"\u25d0";});}catch(e){}})();</script>
"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../blog/">Blog</a>
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>"""

BLOG_FAQ_DONE = True
ARTICLES = [
    {
        "slug": "kolkata-to-digha-bus-guide",
        "title": "বাসে কলকাতা থেকে দীঘা: সময়সূচি এবং একটি প্র্যাকটিক্যাল ট্রাভেল গাইড",
        "desc": "কলকাতা থেকে দীঘা যাওয়ার বাসের সময়সূচি, ভাড়া ও ভ্রমণের টিপস — সকালের SBSTC বাস থেকে এসি বাস পর্যন্ত সব তথ্য এক জায়গায়।",
        "date": "2026-09-18",
        "excerpt": "সমুদ্রের ধারে একটা উইকেন্ড কাটাতে হলে দু'সপ্তাহ আগে ট্রেনের টিকিটের দরকার নেই — সকাল থেকেই কলকাতা থেকে দীঘার বাস ছাড়ে।",
        "related": [
            ("../bus-time-table/kolkata-to-digha.html", "কলকাতা → দীঘা রুট পেজ"),
            ("../bus-time-table/digha-to-kolkata.html", "দীঘা → কলকাতা (ফেরার বাস)"),
            ("../via/digha.html", "দীঘা স্টপ — সব বাসের টাইম"),
        ],
        "faq": [('What time do morning buses leave Kolkata for Digha?', 'SBSTC buses leave around 6:30, 7:00 and 7:30 AM from the Esplanade area; private AC coaches such as Jackson leave around 8:00 AM.'), ('How long does the Kolkata to Digha bus journey take?', 'About four to four and a half hours, depending on Bombay Road traffic.'), ('Are there AC buses from Kolkata to Digha?', 'Yes — private AC coaches run on this route alongside SBSTC government buses.'), ('Do I need to book tickets in advance?', 'Advance booking is not required; reach the counter about 30 minutes early on Fridays, Saturdays and holiday seasons.'), ('When do return buses leave Digha?', 'Return buses start very early in the morning; confirm the last bus time at the Digha stand counter before evening.'), ('কলকাতা থেকে দীঘার সকালের বাস কটায় ছাড়ে?', 'এসপ্ল্যানেড এলাকা থেকে SBSTC বাস প্রায় ৬:৩০, ৭:০০ ও ৭:৩০-এ ছাড়ে; বেসরকারি এসি কোচ (যেমন Jackson) ৮টার দিকে ছাড়ে।'), ('কলকাতা থেকে দীঘা যেতে কত সময় লাগে?', 'বোম্বে রোডের ট্রাফিকের ওপর নির্ভর করে প্রায় চার থেকে সাড়ে চার ঘণ্টা।'), ('কলকাতা থেকে দীঘায় কি এসি বাস আছে?', 'হ্যাঁ — SBSTC সরকারি বাসের পাশাপাশি বেসরকারি এসি কোচও চলে।'), ('আগে থেকে টিকিট বুক করতে হবে কি?', 'তেমন দরকার নেই; শুক্র-শনিবার ও ছুটির মৌসুমে কাউন্টারে আধ ঘণ্টা আগে পৌঁছান।'), ('দীঘা থেকে ফেরার বাস কখন?', 'ফেরার বাস খুব সকালেই ছাড়ে; বিকেলের আগেই কাউন্টার থেকে শেষ বাসের সময় নিশ্চিত করে নিন।')],
        "body": """<p>দীঘায় সমুদ্রের ধারে একটা উইকেন্ড কাটানো আমাদের বাঙালিদের কাছে প্রায় একটা রুটিন হয়ে দাঁড়িয়েছে। আর ভালো খবর হলো, সেখানে যাওয়ার জন্য দু'সপ্তাহ আগে থেকে ট্রেনের টিকিট বুক করার কোনো দরকার নেই। সকাল থেকেই কলকাতা থেকে বাস ছাড়তে থাকে, আর সময়মতো পৌঁছালে দুপুরের খাবারের আগেই আপনি সমুদ্রের জলে পা ডুবিয়ে দিতে পারবেন।</p>
<h2>দীঘার বাসগুলো কেমন?</h2>
<p>বেশিরভাগ যাত্রী এসবিএসটিসি (SBSTC) সরকারি বাসের ওপর নির্ভর করেন যেগুলো এসপ্ল্যানেড এলাকা থেকে ছাড়ে। সকালে প্রায় ৬:৩০, ৭:০০ এবং ৭:৩০-এর বাস পাওয়া যায়, আর এর ভাড়াও বেশ সাধ্যের মধ্যে। আপনি যদি একটু বেশি আরাম চান, তবে এই রুটে প্রাইভেট এসি বাসও চলে। উদাহরণস্বরূপ, জ্যাকসন (Jackson) সকাল ৮টার দিকে এসি কোচ নিয়ে কলকাতা থেকে ছাড়ে। বোম্বে রোডের ট্রাফিকের ওপর নির্ভর করে বেশিরভাগ বাস প্রায় চার থেকে সাড়ে চার ঘণ্টার মধ্যে দীঘায় পৌঁছায়।</p>
<h2>নিয়মিত যাত্রীদের কাছ থেকে কিছু প্র্যাকটিক্যাল টিপস</h2>
<p>পারলে একটু তাড়াতাড়ি বেরোন। সকাল ৭টা বা ৮টার মধ্যে রওনা দিলে আপনি দুপুরের মধ্যে আরামে দীঘায় পৌঁছে যেতে পারবেন, আর পুরো বিকেলটা সমুদ্রসৈকতে কাটানোর সুযোগ পাবেন। শুক্রবার এবং শনিবারের বাসগুলো খুব তাড়াতাড়ি ভর্তি হয়ে যায়, বিশেষ করে গরমের ছুটিতে এবং বড়দিনের সময় দীঘা সিজনে। তাই কাউন্টারে ত্রিশ মিনিট আগে পৌঁছানোটা বুদ্ধিমানের কাজ। রাস্তায় টোল এবং চা পানের বিরতির জন্য কিছু খুচরো টাকা হাতের কাছে রাখুন, আর এসি কোচের জন্য একটা হালকা শাল বা জ্যাকেট সাথে রাখুন, কারণ ওগুলো সত্যিই খুব ঠান্ডা থাকে।</p>
<p>শুধু ছাড়ার সময়টা দেখলেই হবে না। BusJatri-তে আপনি বাসের পথে পড়া প্রতিটি স্টপেজ, প্রতিটি স্টপে পৌঁছানোর সময় এবং একই রুটের বিকল্প বাসগুলোও দেখতে পারবেন, তাই আপনি যদি একটা বাস মিসও করেন, তবে পরের বাসটা ঠিক কখন আসবে তা আপনি সহজেই জানতে পারবেন।</p>
<h2>দীঘা থেকে ফেরা</h2>
<p>দীঘা বাসস্ট্যান্ড থেকে কলকাতার ফেরার বাসগুলো খুব সকালে ছাড়ে। আপনি যদি সমুদ্রের ধারে একটা আরামদায়ক দিন কাটাতে চান এবং একই দিনে ফিরতে চান, তবে বিকেলের কোনো বাসে ওঠার পরিকল্পনা করুন। আর সৈকতে বেশি সময় কাটানোর আগে বাসস্ট্যান্ডের কাউন্টার থেকে শেষ বাসের ছাড়ার সময়টা একবার নিশ্চিত করে নিন।</p>
<p>শেষ একটা কথা: ঋতু এবং রাস্তার অবস্থার ওপর ভিত্তি করে সময়সূচি বদলে যেতে পারে। BusJatri-তে দেওয়া সময়সূচিগুলো নিয়মিত আপডেট করা হয়, তবে ভ্রমণের আগে কাউন্টার বা অপারেটরের সাথে একবার নিশ্চিত হয়ে নিলে কোনো ক্ষতি নেই। আপনার যাত্রা শুভ হোক, আর দীঘা বিচে সবুজ ডাবের জল খেতে ভুলবেন না।</p>""",
    },
    {
        "slug": "jangalmahal-bus-routes",
        "title": "ঝাড়গ্রাম, খাতড়া এবং মানবাজার: জঙ্গলমহল এলাকার বাস রুট",
        "desc": "জঙ্গলমহলের বাসপথ — ঝাড়গ্রাম থেকে মানবাজার, খাতড়া জংশন আর কলকাতার সরাসরি বাসের সময়সূচি ও বাস্তব অভিজ্ঞতার গাইড।",
        "date": "2026-09-18",
        "excerpt": "শালবন আর লাল মাটির রাস্তার জঙ্গলমহলে বাসই জীবনরেখা — কোন সময়ে কোন বাস, সব এক জায়গায়।",
        "related": [
            ("../bus-time-table/jhargram-to-manbazar.html", "ঝাড়গ্রাম → মানবাজার রুট পেজ"),
            ("../via/khatra.html", "খাতড়া স্টপ — সব বাসের টাইম"),
            ("../bus-time-table/kolkata-to-manbazar.html", "কলকাতা → মানবাজার"),
            ("../bus-time-table/purulia-to-manbazar.html", "পুরুলিয়া → মানবাজার"),
            ("../bus-time-table/barabazar-to-purulia.html", "বড়বাজার → পুরুলিয়া"),
        ],
        "faq": [('When do morning buses leave Jhargram for Manbazar and Khatra?', 'Around 4:50 AM (Badsha) and 5:00 AM (Monami Travels); an AC bus leaves around 5:30 AM.'), ('Are there direct buses from Kolkata to the Jangalmahal area?', 'Yes — Mahamaya Super Fast style buses leave Kolkata around 4:30 AM for Khatra, Ranibandh and Manbazar.'), ('Why is Khatra a useful junction?', 'Buses towards Bankura, Purulia, Medinipur and Bardhaman pass through Khatra — change there if you miss a direct village bus.'), ('How is bus travel in the monsoon?', 'Forest roads can be slow in the rains; keep extra time and confirm schedules locally.'), ('Where can I check timings for Jangalmahal routes?', 'BusJatri route pages and the Khatra stop page list every bus with its arrival time at each stop.'), ('ঝাড়গ্রাম থেকে মানবাজার/খাতড়ার সকালের বাস কখন?', 'প্রায় ৪:৫০-এ বাদশা, ৫:০০-এ মনামী ট্রাভেলস; সাড়ে ৫টার দিকে একটি এসি বাসও ছাড়ে।'), ('কলকাতা থেকে জঙ্গলমহলে সরাসরি বাস আছে কি?', 'হ্যাঁ — মহামায়া সুপার ফাস্ট ধরনের বাস ভোর ৪:৩০-এর দিকে কলকাতা থেকে ছাড়ে।'), ('খাতড়া জংশন কেন গুরুত্বপূর্ণ?', 'বাঁকুড়া, পুরুলিয়া, মেদিনীপুর ও বর্ধমানের বাস খাতড়া দিয়েই যায় — সরাসরি বাস মিস হলে খাতড়ায় বাস বদলান।'), ('বর্ষাকালে যাত্রা কেমন?', 'জঙ্গলের রাস্তা ধীরগতির হতে পারে; বাড়তি সময় হাতে রাখুন, স্থানীয়ভাবে সময় জেনে নিন।'), ('এই রুটগুলোর সময়সূচি কোথায় দেখব?', 'BusJatri-র রুট পেজ ও খাতড়া স্টপ পেজে প্রতিটি বাসের সময় দেওয়া আছে।')],
        "body": """<p>শালবন, লাল মাটির রাস্তা আর ছোট ছোট শহর নিয়ে জঙ্গলমহল এলাকাটি আমাদের রাজ্যের এক সুন্দর অংশ, যার কথা বেশিরভাগ ট্রাভেল গাইডে খুব একটা বলা থাকে না। কিন্তু সেখানে বসবাসকারী মানুষদের জন্য এবং এই শান্ত কোণটি ভালোবাসেন এমন পর্যটকদের জন্য বাসই হলো জীবনরেখা। এই অঞ্চলে বাস ভ্রমণ আসলে কেমন, তার একটা চিত্র নিচে দেওয়া হলো।</p>
<h2>ঝাড়গ্রাম থেকে সকালের বাস</h2>
<p>আপনি যদি ঝাড়গ্রাম থেকে মানবাজার এবং খাতড়ার দিকে যান, তবে সকালের সময়টা আপনার জন্য সবচেয়ে ভালো। সকাল ৪:৫০-এর দিকে বাদশা বাস ছাড়ে, এরপর সকাল ৫:০০ টার দিকে মনামী ট্রাভেলস। সকাল সাড়ে ৫-টার দিকে একটি এসি বাসের সুবিধাও আছে, যা গ্রীষ্মের গরমে বেশ স্বস্তিদায়ক। এই রুটটি জঙ্গল এবং সারেঙ্গা-র মতো ছোট স্টেশনগুলোর মধ্যে দিয়ে যায়, আর জানলা দিয়ে আসা সকালের বাতাস শহরের মানুষ টাকার বিনিময়েও পেতে চায়।</p>
<h2>কলকাতা থেকে আসা</h2>
<p>কলকাতা থেকেও এই এলাকার দিকে সরাসরি বাস পরিষেবা রয়েছে। মহামায়া সুপার ফাস্ট স্টাইলের বাসগুলো ভোর ৪:৩০-এর দিকে কলকাতা থেকে ছাড়ে এবং সকালের শেষের দিকে জঙ্গলমহলের শহরগুলোতে পৌঁছায়। এই দীর্ঘ রুটগুলো কলকাতা থেকে খাতড়া, রানীবাঁধ এবং মানবাজারের মতো জায়গাগুলোর সাথে যুক্ত, আর গ্রামের বাড়ি ফেরা পরিবারগুলোর কাছে এগুলো খুবই জনপ্রিয়।</p>
<h2>খাতড়া হলো জংশন</h2>
<p>এই অঞ্চলের অনেক গ্রামের জন্য খাতড়া একটি প্রধান জংশন হিসেবে কাজ করে। বাঁকুড়া, পুরুলিয়া, মেদিনীপুর এবং বর্ধমানের দিকে যাওয়া বাসগুলো এখান দিয়েই যায়। আপনার গ্রামের দিকে যাওয়ার কোনো ডাইরেক্ট বাস মিস করলে, আগে খাতড়ায় পৌঁছে সেখান থেকে বাস বদলানোই সাধারণত সবচেয়ে বুদ্ধিমানের কাজ। BusJatri-তে আপনি খাতড়ার মধ্যে দিয়ে যাওয়া প্রতিটি বাস দেখতে পারবেন, যেখানে বাসটি খাতড়ায় পৌঁছানোর সময় এবং কোথায় যাচ্ছে, তা এক পৃষ্ঠাতেই পাওয়া যায়।</p>
<h2>কিছু সত্যি কথা</h2>
<p>ঋতু পরিবর্তনের সাথে সাথে এই অঞ্চলের সময়সূচি কিছুটা বদলে যায়, আর বর্ষাকালে জঙ্গল রাস্তাগুলো ধীরগতির হতে পারে। বাস কন্ডাক্টর এবং স্থানীয় যাত্রীরাই তথ্যের সবচেয়ে নির্ভরযোগ্য উৎস, তাই জিজ্ঞেস করতে দ্বিধা করবেন না। এছাড়া, ভেতরের দিকের এলাকাগুলোতে সকালের বাসগুলোতে রোজকার যাত্রী এবং ছাত্রছাত্রীদের ভিড় থাকতে পারে, তাই আপনি যদি বড় লাগেজ নিয়ে যান, তবে একটু আগে রওনা দিলে আপনার যাত্রা আরও আরামদায়ক হবে।</p>
<h2>আপনাদের কাছে আমাদের অনুরোধ</h2>
<p>আপনি যদি এই রুটগুলোতে ভ্রমণ করেন এবং আমাদের তালিকা থেকে কোনো বাস বাদ পড়তে দেখেন, অথবা কোনো সময়সূচি বদলে যেতে দেখেন, তবে আমাদের ফেসবুক পেজ বা কন্ট্যাক্ট ইমেলের মাধ্যমে আমাদের জানান। BusJatri আপনাদের মতো যাত্রীদের তথ্য দিয়েই বড় হয়, আর প্রতিটি ছোট সংশোধন পরবর্তী যাত্রীকে সাহায্য করে।</p>""",
    },
    {
        "slug": "how-to-find-bus-timings",
        "title": "BusJatri-তে কীভাবে সহজেই বাসের সময় বের করবেন",
        "desc": "BusJatri সাইট ব্যবহারের সহজ গাইড — রুট খোঁজা, নতুন স্টপ পেজ, বাংলা ও ইংরেজি সার্চ — ঠিক যেভাবে একজন বন্ধু বুঝিয়ে বলবেন।",
        "date": "2026-09-18",
        "excerpt": "তাড়ার মধ্যে, ছোট ডেটা প্যাক নিয়ে ফোনে বাসের সময় খুঁজছেন? এই গাইডটি আপনার জন্যই।",
        "related": [
            ("../bus-time-table/", "সব রুটের তালিকা"),
            ("../via/", "সব স্টপ পেজ A–Z"),
            ("../index.html", "হোমপেজে সার্চ করুন"),
        ],
        "faq": [('How do I search for a bus route on BusJatri?', 'Type your start or destination in the homepage search box — suggestions appear in Bengali and English, and tapping a route shows every bus with times, operator and bus type.'), ('What is a stop page?', 'Every stop has its own page: a departure board of every bus passing that stop from early morning to late night. Over 2,600 stop pages are live.'), ('Can I search in Bengali?', 'Yes — search and suggestions work in both Bengali and English.'), ('Does BusJatri need an account or payment?', 'No — it is free, login-free, and light enough to work on slow connections.'), ('What if I find a wrong time or a missing bus?', 'Tell us on our Facebook page or by email — most corrections come from passengers, drivers and bus stand staff.'), ('BusJatri-তে বাসের রুট কীভাবে খুঁজব?', 'হোমপেজের সার্চ বক্সে যাত্রা শুরু বা গন্তব্যের নাম লিখুন — বাংলা ও ইংরেজি দুই ভাষাতেই সাজেশন আসবে, রুটে ট্যাপ করলেই সময় সহ সব বাসের তালিকা।'), ('স্টপ পেজ কী?', 'প্রতিটি স্টপের নিজস্ব পেজ — ভোর থেকে গভীর রাত পর্যন্ত ওই স্টপ দিয়ে যাওয়া সব বাসের ডিপারচার বোর্ড। এখনই ২,৬০০-র বেশি স্টপ পেজ চালু।'), ('বাংলায় সার্চ করা যায়?', 'হ্যাঁ — বাংলা ও ইংরেজি দুই ভাষাতেই সার্চ ও সাজেশন কাজ করে।'), ('অ্যাকাউন্ট বা টাকা লাগে কি?', 'না — সাইট সম্পূর্ণ বিনামূল্যে, লগইন ছাড়াই, আর ধীর ইন্টারনেটেও ভালো চলে।'), ('ভুল সময় বা বাদ পড়া বাস দেখলে?', 'ফেসবুক পেজ বা ইমেলে জানান — বেশিরভাগ সংশোধন যাত্রী, চালক ও স্ট্যান্ডের কর্মীদের কাছ থেকেই আসে।')],
        "body": """<p>প্রতিদিন পশ্চিমবঙ্গের শত শত মানুষ তাদের ফোনে বাসের সময় খোঁজেন, সাধারণত তাড়া থাকে, আর সাধারণত ছোট ডেটা প্যাক থাকে। BusJatri ঠিক এই মুহূর্তগুলোর জন্যই তৈরি করা হয়েছে। সাইটটি কীভাবে ব্যবহার করবেন তার একটি সহজ গাইড নিচে দেওয়া হলো, ঠিক যেভাবে একজন বন্ধু আপনাকে বুঝিয়ে বলবেন।</p>
<h2>রুট খোঁজা</h2>
<p>হোমপেজে আপনি একটি সার্চ বক্স পাবেন। আপনার শুরুর জায়গা বা গন্তব্যের নাম টাইপ করুন। টাইপ করার সাথে সাথে নিচে বাংলা এবং ইংরেজি উভয় ভাষাতেই সাজেশন আসবে। আপনার জায়গাটি বেছে নিন, এবং আপনি এর সাথে সম্পর্কিত সব রুট দেখতে পাবেন। যেকোনো রুটে ট্যাপ করলেই আপনি বাস ছাড়ার সময়, পৌঁছানোর সময়, অপারেটরের নাম এবং বাসের ধরন (সরকারি, বেসরকারি বা এসি) সহ বাসের পুরো তালিকা পেয়ে যাবেন।</p>
<h2>স্টপ পেজ, আমাদের নতুন ফিচার</h2>
<p>সম্প্রতি আমরা এমন কিছু যোগ করেছি যা নিয়ে আমরা বেশ গর্বিত। এখন প্রতিটি স্টপের নিজস্ব পেজ রয়েছে। ধরুন আপনি খাতড়া, দীঘা বা এসপ্ল্যানেডে দাঁড়িয়ে আছেন এবং আজ সেই স্টপ দিয়ে যাওয়া প্রতিটি বাস সম্পর্কে জানতে চান, তাহলে শুধু স্টপ পেজটি খুলুন। আপনি খুব সকাল থেকে গভীর রাত পর্যন্ত সাজানো একটি সম্পূর্ণ ডিপারচার বোর্ড দেখতে পাবেন, যেখানে প্রতিটি বাসের নাম, আপনার স্টপে পৌঁছানোর সময় এবং এটি কোথায় যাচ্ছে তা লেখা থাকবে। এটি অনেকটা স্টেশনের বোর্ডে দেখার মতো, তবে বাসের জন্য। ইতিমধ্যেই দুই হাজার ছয়শোর বেশি স্টপ পেজ চালু হয়ে গেছে।</p>
<p>যেকোনো রুট পেজ থেকে, তালিকায় দেখানো স্টপের নামগুলোতেও ট্যাপ করা যায়, তাই আপনি একটি রুট থেকে এর যেকোনো স্টপে যেতে পারেন এবং সেখান থেকে আরও কানেকশন খুঁজে দেখতে পারেন।</p>
<h2>কিছু ছোট জিনিস যা সাহায্য করে</h2>
<p>পেজগুলো হালকা হওয়ায়, সাইটটি ধীরগতির ইন্টারনেটেও ভালো কাজ করে। সবকিছু বিনামূল্যে এবং লগইনের কোনো প্রয়োজন নেই। আর যদি আপনার কোনো বাস বাদ পড়া বা ভুল সময় দেখেন, তবে আমাদের জানান। আমাদের অনেক সংশোধন যাত্রীদের, চালকদের এবং বাস স্ট্যান্ডের কর্মীদের কাছ থেকে আসে, যারা ফেসবুকে আমাদের মেসেজ করেন। কমিউনিটির তথ্য এই সাইটটিকে সচল রাখে।</p>
<h2>ভ্রমণের আগে একটি অনুরোধ</h2>
<p>সময়সূচি বদলায়, বাসগুলো রুট পরিবর্তন করে, এবং বর্ষাকালে রাস্তার কারণে সবকিছু ধীর হয়ে যায়। পরিকল্পনা করার জন্য BusJatri ব্যবহার করুন, তবে গুরুত্বপূর্ণ যাত্রার জন্য সবসময় বাস স্ট্যান্ডের কাউন্টার বা অপারেটরের সাথে সঠিক সময় নিশ্চিত হয়ে নিন। আমরা আপডেট থাকার সর্বোচ্চ চেষ্টা করি, তবে দুই মিনিটের একটি কনফার্মেশন কল আপনার এক ঘণ্টার অপেক্ষা বাঁচাতে পারে।</p>""",
    },
    {
        "slug": "purulia-to-manbazar-bus-timetable",
        "title": "পুরুলিয়া থেকে মানবাজার বাস টাইমটেবিল: সম্পূর্ণ গাইড",
        "desc": "পুরুলিয়া-মানবাজার রুটের সকাল থেকে দুপুর পর্যন্ত সব বাসের সময়সূচি — রাজপুত, সৌরভ, মা বাসন্তী, মনালিষা সহ স্থানীয় টিপস।",
        "date": "2026-09-18",
        "excerpt": "মানবাজার রুটে সকাল ৫:৪০ থেকে দুপুর ১:৫০ পর্যন্ত বাস — কোন সময়ে কোন বাস, সম্পূর্ণ তালিকা।",
        "related": [
            ("../bus-time-table/purulia-to-manbazar.html", "পুরুলিয়া → মানবাজার রুট পেজ"),
            ("../bus-time-table/manbazar-to-purulia.html", "মানবাজার → পুরুলিয়া রুট পেজ"),
            ("../via/manbazar.html", "মানবাজার স্টপ — সব বাসের টাইম"),
            ("../via/purulia.html", "পুরুলিয়া স্টপ — সব বাসের টাইম"),
        ],
        "faq": [('What is the first bus from Manbazar to Purulia?', 'The Rajput service starts around 5:40 AM, followed by Sourav around 6:40 AM.'), ('Which buses run between 8 and 9 AM?', 'Bhabhalakshmi (~8:20 AM), Sri Shyam (~8:25 AM) and Maa Basanti (~8:50 AM).'), ('Are there buses later in the day?', 'Yes — Maa Chhinnamasta around 11:10 AM, Rajput at 12:15 PM and Monalisha at 1:50 PM.'), ('When does the first bus leave Purulia for Manbazar?', 'The Suman bus leaves Purulia around 7:00 AM; returning Manbazar-Purulia buses also pick up passengers in the evening.'), ('Are market days crowded?', 'Yes — Mondays and other haat days fill up early with little luggage space; plan accordingly.'), ('মানবাজার থেকে পুরুলিয়ার প্রথম বাস কটায়?', 'রাজপুত সার্ভিস প্রায় ৫:৪০-এ, এরপর সৌরভ প্রায় ৬:৪০-এ ছাড়ে।'), ('সকাল ৮টা থেকে ৯টার মধ্যে কোন কোন বাস?', 'ভাগ্যলক্ষ্মী (প্রায় ৮:২০), শ্রী শ্যাম (প্রায় ৮:২৫) এবং মা বাসন্তী (প্রায় ৮:৫০)।'), ('দুপুরের দিকে কি বাস আছে?', 'হ্যাঁ — মা ছিন্নমস্তা প্রায় ১১:১০-এ, রাজপুত ১২:১৫-এ এবং মনালিষা ১:৫০-এ।'), ('পুরুলিয়া থেকে মানবাজারের প্রথম বাস কটায়?', 'সুমন বাস সকাল ৭টার দিকে ছাড়ে; ফেরার পথে সন্ধ্যায়ও বাস পাওয়া যায়।'), ('বাজারের দিনে ভিড় বেশি হয়?', 'হ্যাঁ — সোমবার ও অন্য হাটের দিনে বাস তাড়াতাড়ি ভরে যায়, মালপত্রের জায়গা কম থাকে।')],
        "body": """<p>পুরুলিয়া থেকে মানবাজার রুটটি মানবাজার মহকুমা এলাকার অন্যতম ব্যস্ত রুট। প্রতিদিন ছাত্র, অফিসযাত্রী, ব্যবসায়ী এবং গ্রামের মানুষ এই রুটে যাতায়াত করেন, আর বাজারের দিনগুলোতে প্রথম বাস থেকেই বাসগুলো কানায় কানায় পূর্ণ থাকে। স্থানীয় যাত্রীরা এই রুটের বাসগুলোর সময়সূচি যেভাবে জানেন, তার একটি সম্পূর্ণ চিত্র নিচে দেওয়া হলো।</p>
<h2>মানবাজার থেকে পুরুলিয়াগামী সকালের বাস</h2>
<p>প্রথম বাসটি মানবাজার থেকে খুব ভোরে ছেড়ে যায়। রাজপুত সার্ভিসটি সকাল ৫:৪০ নাগাদ শুরু হয়, এরপর সৌরভ বাসটি ছাড়ে প্রায় ৬:৪০-এ। এরপর ভাগ্যলক্ষ্মী এবং শ্রী শ্যাম বাস দুটি ছাড়ে যথাক্রমে ৮:২০ এবং ৮:২৫ নাগাদ, আর মা বাসন্তী ছাড়ে প্রায় ৮:৫০-এ। তাই সকাল ৫:৪০ থেকে ৯টার মধ্যে মোটামুটি প্রতি আধ ঘণ্টা থেকে এক ঘণ্টা অন্তর বাস পাওয়া যায়, যা সকালের কাজের জন্য পুরুলিয়া শহরে পৌঁছাতে খুব সুবিধাজনক। দিনের পরের দিকে, মা ছিন্নমস্তা বাসটি সকাল ১১:১০ নাগাদ চলে, আর দুপুরের পর ১২:১৫-এর রাজপুত সার্ভিস এবং ১:৫০-এর মনালিষা বাসটি পাওয়া যায়।</p>
<h2>পুরুলিয়া থেকে মানবাজারগামী বাস</h2>
<p>উল্টো দিক থেকে, সুমন বাসটি সকাল ৭:০০ নাগাদ পুরুলিয়া থেকে ছাড়ে। এর পাশাপাশি, মানবাজার-পুরুলিয়া বাসগুলোর ফেরার পথেও বিকেলে পুরুলিয়া থেকে যাত্রীরা ওঠেন, তাই এই রুটে সারাদিনই বাস পাওয়ার সুযোগ থাকে। প্রতিটি সার্ভিসের বর্তমান সময়সূচি দেখতে BusJatri-এর রুট পেজটি দেখতে পারেন, যেখানে প্রথম বাস, শেষ বাস এবং বাস থামার সময়গুলো এক জায়গায় দেওয়া থাকে।</p>
<h2>পথে বাস থামার জায়গা</h2>
<p>এই রুটটি মানবাজার এলাকার ছোট ছোট শহর এবং হাটগুলোর মধ্যে দিয়ে যায়। বাসগুলো সাধারণত প্রধান স্ট্যান্ডগুলোতে থামে, এবং ছোট জায়গাগুলোতে রাস্তার ধার থেকেও যাত্রীদের তোলে। আপনি যদি পথে কোনো গ্রাম থেকে বাসে ওঠেন, তবে একটু আগে রাস্তার ধারে পৌঁছে যাবেন, কারণ এই বাসগুলো সবসময় বেশি সময় ধরে থামে না।</p>
<h2>কিছু স্থানীয় টিপস</h2>
<p>সোমবার এবং অন্যান্য বাজারের দিনগুলোতে বাসে ভিড় বেশি থাকে, আর মালপত্র রাখার জায়গা কম থাকে, তাই সেই অনুযায়ী পরিকল্পনা করুন। বর্ষাকালে পুরুলিয়া ও মানবাজারের মধ্যে রাস্তার অবস্থা খারাপ থাকার কারণে বাসগুলো ধীরগতিতে চলতে পারে, তাই জরুরি কাজের জন্য কিছুটা বাড়তি সময় হাতে রাখুন। আর যদি আপনার কাছে বাস স্টাফের ফোন নম্বর থাকে, তবে সেটি সেভ করে রাখুন, কারণ অনেক রুটে বাস চলছে কি না তা স্টাফরা ফোনে জানিয়ে দেন।</p>
<p>ঋতু, জ্বালানির দাম এবং রাস্তার অবস্থার ওপর ভিত্তি করে সময়সূচি বদলে যেতে পারে। BusJatri-তে সময়সূচি নিয়মিত আপডেট করা হয়, তবে কোনো জরুরি যাত্রার আগে পুরুলিয়া বা মানবাজার বাস স্ট্যান্ডের কাউন্টারে সময়টা নিশ্চিত করে নিন। BusJatri-তে পুরুলিয়া এবং মানবাজার হয়ে যাওয়া প্রতিটি বাসের স্টপ পেজেও তথ্য দেওয়া থাকে, তাই আপনি একই স্ট্যান্ড থেকে অন্যান্য গন্তব্যে যাওয়া বাসগুলোও খুঁজে পেতে পারেন।</p>""",
    },
]


def article_page(a):
    import html as _h
    related = "".join(
        f'<a class="rel-chip" href="{href}">{_h.escape(label)}</a>' for href, label in a["related"]
    )
    faq_html = ""
    faq_schema = ""
    if a.get("faq"):
        import json as _j
        items = "".join(
            "<details" + (" open" if i == 0 else "") + ' style="border:1px solid var(--line,rgba(33,28,22,.15));border-radius:10px;padding:10px 14px;margin:8px 0;background:var(--surface,#fffcf4)">' + '<summary style="cursor:pointer;font-weight:600;font-size:.95rem">' + q + "</summary>" + '<p style="margin:8px 0 0;font-size:.9rem;line-height:1.7;color:var(--ink-dim,#665)">' + ans + "</p></details>"
            for i, (q, ans) in enumerate(a["faq"]))
        faq_html = ('<section class="seo-section" style="margin-top:26px"><h3 class="section-title">FAQ</h3>' + items + "</section>")
        faq_schema = ('<script type="application/ld+json">' + _j.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": an}} for q, an in a["faq"]]}, ensure_ascii=False) + "</script>")
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{a["title"]} | BusJatri</title>
<meta name="description" content="{a["desc"]}">
<link rel="canonical" href="{BASE}/blog/{a["slug"]}.html">
<meta property="og:title" content="{a["title"]} | BusJatri">
<meta property="og:description" content="{a["desc"]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/blog/{a["slug"]}.html">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{faq_schema}{GA4}<style>.article-body p{{line-height:1.85;font-size:1rem;color:var(--ink,#222);margin:0 0 16px}}.article-body h2{{font-size:1.18rem;margin:28px 0 12px;color:var(--ink,#222)}}.article-meta{{font-size:.82rem;color:var(--ink-dim,#665);margin:6px 0 18px}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}</style>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">Blog</a> › <span>{a["title"][:34]}…</span></div>
<article>
<h1 style="font-size:1.5rem;line-height:1.35;margin:14px 0 4px">{a["title"]}</h1>
<div class="article-meta">{a["date"]} · BusJatri টিম</div>
<div class="article-body">
{a["body"]}
</div>
</article>
{faq_html}
<section class="seo-section" style="margin-top:26px">
  <h3 class="section-title">Related Pages</h3>
  <div class="chip-row">{related}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="./">📚 All Posts</a>
</section>
</main>
{FOOTER}
</body>
</html>
"""


def manifest_articles():
    """Daily auto-generated route posts (data/blog-manifest.json)."""
    import json
    p = ROOT / "data" / "blog-manifest.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def index_page():
    import html as _h
    all_posts = manifest_articles() + ARTICLES
    all_posts.sort(key=lambda a: a["date"], reverse=True)
    cards = ""
    for a in all_posts:
        cards += f"""<a class="bus-row" href="{a["slug"]}.html" style="display:block">
  <div class="bmid">
    <div class="op" style="font-size:1rem">{a["title"]}</div>
    <div class="mrow" style="margin-top:6px"><span>{a["date"]}</span></div>
    <p style="margin:8px 0 0;font-size:.9rem;color:var(--ink-dim,#665);line-height:1.6">{a["excerpt"]}</p>
  </div>
</a>"""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog — Bus Travel Guides | BusJatri</title>
<meta name="description" content="West Bengal bus travel guides: route timetables, first and last bus timings, operators and travel tips from BusJatri.">
<link rel="canonical" href="{BASE}/blog/">
<meta property="og:title" content="Blog — Bus Travel Guides | BusJatri">
<meta property="og:description" content="West Bengal bus travel guides: route timetables, operators and travel tips from BusJatri.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#b8791f">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b8791f' stroke-width='2'%3E%3Cpath d='M4 16V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10'/%3E%3Cpath d='M4 16h16'/%3E%3C/svg%3E">
<link rel="stylesheet" href="../css/seo.css">
<link rel="stylesheet" href="../css/extras.css">
{GA4}<style>.bus-row{{display:block;margin-bottom:14px}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}</style>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <span>Blog</span></div>
<div class="seo-hero">
  <h1>Blog <span class="arr">—</span> Bus Travel Guides</h1>
  <p class="bn-sub">West Bengal bus routes, timetables and travel tips</p>
</div>
{cards}
</main>
{FOOTER}
</body>
</html>
"""


def main():
    dry = "--write" not in sys.argv
    if not dry:
        bdir = ROOT / "blog"
        bdir.mkdir(exist_ok=True)
        for a in ARTICLES:
            (bdir / (a["slug"] + ".html")).write_text(article_page(a), encoding="utf-8")
        (bdir / "index.html").write_text(index_page(), encoding="utf-8")
        print(f"blog: {len(ARTICLES)} articles + index written")

        # homepage footer: blog link (idempotent)
        hp = ROOT / "index.html"
        s = hp.read_text(encoding='utf-8')
        if 'href="blog/"' not in s:
            anchor = '<a href="about.html">About Us</a>'
            if anchor in s:
                s = s.replace(anchor, '<a href="blog/">Blog</a>\n      ' + anchor, 1)
                hp.write_text(s, encoding="utf-8")
                print("homepage: blog link added to footer")

        # sitemap: blog urls (idempotent)
        sm = ROOT / "sitemap.xml"
        s = sm.read_text(encoding="utf-8")
        s = re.sub(r"<url><loc>" + re.escape(BASE) + r"/blog/[^<]*</loc>.*?</url>\n?", "", s)
        add = f"<url><loc>{BASE}/blog/</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n"
        for a in manifest_articles() + ARTICLES:
            add += f"<url><loc>{BASE}/blog/{a['slug']}.html</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\n"
        s = s.replace("</urlset>", add + "</urlset>")
        sm.write_text(s, encoding="utf-8")
        print("sitemap: blog urls added")


if __name__ == "__main__":
    main()
