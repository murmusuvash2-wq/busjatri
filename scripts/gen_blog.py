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
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="footer">
  <div class="container">
    <div style="display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:center;font-size:13px">
      <a href="../blog/">ব্লগ</a>
      <a href="../about.html">About Us</a>
      <a href="../contact.html">Contact Us</a>
      <a href="../privacy-policy.html">Privacy Policy</a>
    </div>
    <p style="margin:14px 0 0;text-align:center">BusJatri — West Bengal Bus Timetable</p>
    <p style="margin:6px 0 0;text-align:center">Contact: busjatri@zohomail.in</p>
  </div>
</footer>"""

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
        ],
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
]


def article_page(a):
    import html as _h
    related = "".join(
        f'<a class="rel-chip" href="{href}">{_h.escape(label)}</a>' for href, label in a["related"]
    )
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
{GA4}<style>.article-body p{{line-height:1.85;font-size:1rem;color:var(--ink,#222);margin:0 0 16px}}.article-body h2{{font-size:1.18rem;margin:28px 0 12px;color:var(--ink,#222)}}.article-meta{{font-size:.82rem;color:var(--ink-dim,#665);margin:6px 0 18px}}a.bus-row,a.bus-row:visited{{color:inherit;text-decoration:none}}</style>
</head>
<body>
{HEADER}
<main class="container seo-main" style="padding-top:18px;padding-bottom:48px;max-width:720px">
<div class="crumbs"><a href="../index.html">Home</a> › <a href="./">ব্লগ</a> › <span>{a["title"][:34]}…</span></div>
<article>
<h1 style="font-size:1.5rem;line-height:1.35;margin:14px 0 4px">{a["title"]}</h1>
<div class="article-meta">{a["date"]} · BusJatri টিম</div>
<div class="article-body">
{a["body"]}
</div>
</article>
<section class="seo-section" style="margin-top:26px">
  <h3 class="section-title">সম্পর্কিত পেজ</h3>
  <div class="chip-row">{related}</div>
</section>
<section class="seo-section">
  <a class="rel-chip" href="./">📚 সব লেখা</a>
</section>
</main>
{FOOTER}
</body>
</html>
"""


def index_page():
    cards = ""
    for a in ARTICLES:
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
<title>ব্লগ — বাস ভ্রমণের গাইড | BusJatri</title>
<meta name="description" content="পশ্চিমবঙ্গের বাস ভ্রমণ নিয়ে BusJatri-র বাংলা ব্লগ — রুট গাইড, সময়সূচি টিপস এবং বাস্তব অভিজ্ঞতা।">
<link rel="canonical" href="{BASE}/blog/">
<meta property="og:title" content="ব্লগ — বাস ভ্রমণের গাইড | BusJatri">
<meta property="og:description" content="পশ্চিমবঙ্গের বাস ভ্রমণ নিয়ে BusJatri-র বাংলা ব্লগ।">
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
<div class="crumbs"><a href="../index.html">Home</a> › <span>ব্লগ</span></div>
<div class="seo-hero">
  <h1>ব্লগ <span class="arr">—</span> বাস ভ্রমণের গাইড</h1>
  <p class="bn-sub">পশ্চিমবঙ্গের বাসপথ নিয়ে বাংলায় লেখা</p>
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
                s = s.replace(anchor, '<a href="blog/">ব্লগ (Blog)</a>\n      ' + anchor, 1)
                hp.write_text(s, encoding="utf-8")
                print("homepage: blog link added to footer")

        # sitemap: blog urls (idempotent)
        sm = ROOT / "sitemap.xml"
        s = sm.read_text(encoding="utf-8")
        s = re.sub(r"<url><loc>" + re.escape(BASE) + r"/blog/[^<]*</loc>.*?</url>\n?", "", s)
        add = f"<url><loc>{BASE}/blog/</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>\n"
        for a in ARTICLES:
            add += f"<url><loc>{BASE}/blog/{a['slug']}.html</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>\n"
        s = s.replace("</urlset>", add + "</urlset>")
        sm.write_text(s, encoding="utf-8")
        print("sitemap: blog urls added")


if __name__ == "__main__":
    main()
