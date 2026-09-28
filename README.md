# MovieBox-TUI (Python Production Port)

> **MovieBox-TUI** এর সম্পূর্ণ পাইথন সংস্করণ (Complete Python Port of `mesamirh/MovieBox-Tui`).
> এটি একটি ক্লিন, মডুলার, এক্সটেনসিবল এবং প্রডাকশন গ্রেড পাইথন প্রজেক্ট যা টার্মিনালে মুভি, টিভি সিরিজ এবং লাইভ আইপিটিভি চ্যানেল স্ট্রিম করতে সাহায্য করে।

---

## 🌟 বৈশিষ্ট্যসমূহ (Features)

1. **MovieBox VIP Core Provider:**
   - OneRoom / WeFeed মোবাইল API রিভার্স-ইঞ্জিনিয়ার্ড সিগনেচার অ্যালগরিদম (`HMAC-MD5` ভিত্তিক `x-tr-signature` এবং `x-client-token`)।
   - হোস্ট পুল অটো-ফেলওভার (`api6.aoneroom.com`, `api5.aoneroom.com`, `api4.aoneroom.com` ইত্যাদি)।
   - অটোমেটিক ভিজিটর লগইন এবং ডিস্ক সেশন ক্যাশিং।
   - ক্লাউডফ্রন্ট সাইনড পলিসি ও কুকি থেকে ডাইরেক্ট DASH (`.mpd`) ও MP4 রেজোলিউশন এক্সট্রাকশন।
2. **মাল্টি-প্রোভাইডার সাপোর্ট (Multi-Provider Architecture):**
   - **MovieBox VIP**: প্রাইমারি হাই-স্পিড ভিআইপি স্ট্রিমার।
   - **Stremio Addons**: সিনেম্যাটা মেটাডাটা ও টরেন্টিও/সাইবারফ্লিক্স স্ট্রিম।
   - **Live TV (IPTV)**: খেলাধুলা (Sports), সংবাদ (News), বিনোদন ও বাংলা লাইভ চ্যানেল (Somoy TV, Jamuna, Channel 24, Independent TV)।
   - **4KHDHub**: 4K ও 1080p হাবক্লাউড ডিরেক্ট লিঙ্ক।
   - **BDIX**: বাংলাদেশ লোকাল মিরর সাপোর্ট ইন্টারফেস।
3. **টার্মিনাল ইউজার ইন্টারফেস (Rich TUI):**
   - ফুল-স্ক্রিন কালারফুল মেনু, সার্চ হিস্ট্রি, টেবিল ও ইন্টারেক্টিভ সিলেকশন।
4. **ভিডিও প্লেয়ার ইন্টিগ্রেশন (Video Player Support):**
   - `mpv`: ডাইরেক্ট অরিজিনাল হেডার (`--http-header-fields`), কুকি ও সাবটাইটেল সাপোর্ট।
   - `vlc`: রেফারার ও ইউজার এজেন্ট ফ্ল্যাগ সহ।
   - বিল্ট-ইন ডাউনলোড ম্যানেজার: মাল্টি-চাঙ্ক প্রগ্রেস বার সহ লোকাল স্টোরেজে ডাউনলোড।

---

## 📁 প্রজেক্ট স্ট্রাকচার (Project Directory Structure)

```
moviebox/
├── main.py                     # মূল এক্সিকিউটেবল ফাইল (CLI & TUI রানার)
├── config.py                   # সেন্ট্রাল কনফিগারেশন, ক্যাশ পাথ, ডিফল্ট সেটিংস
├── requirements.txt            # ডিপেন্ডেন্সি লিস্ট (requests, rich)
├── README.md                   # ডকুমেন্টেশন
│
├── models/                     # ডোমেন ডাটা মডেল (Data Classes)
│   ├── __init__.py
│   ├── media.py                # CatalogItem, MediaDetails, Season, Episode, DubOption
│   ├── release.py              # Release, SourceMirror, SubtitleOption
│   └── tv.py                   # Channel, TVCategory, TVPlaylist
│
├── providers/                  # স্ট্রিম প্রোভাইডার মডিউল
│   ├── __init__.py             # প্রোভাইডার রেজিস্ট্রি (Registry)
│   ├── base.py                 # Abstract BaseProvider ক্লাস
│   │
│   ├── moviebox/               # MovieBox VIP প্রোভাইডার
│   │   ├── __init__.py
│   │   ├── crypto.py           # HMAC-MD5 সিগনেচার, X-Client-Token
│   │   ├── session.py          # JWT পার্সার, ভিজিটর লগইন, ক্যাশ রিফ্রেশ
│   │   ├── client.py           # মাল্টি-হোস্ট ফলব্যাক HTTP ক্লায়েন্ট
│   │   ├── adapt.py            # JSON রেসপন্স অ্যাডাপ্টার ও পলিসি ডিকোড
│   │   └── title.py            # টাইটেল স্যানিটাইজার
│   │
│   ├── addons/                 # Stremio Addon প্রোভাইডার (Cinemeta)
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── adapter.py
│   │
│   ├── tv/                     # Live IPTV প্রোভাইডার
│   │   ├── __init__.py
│   │   ├── parser.py           # M3U / M3U8 প্লেলিস্ট পার্সার ও ক্যাশার
│   │   └── channels.py         # ভেরিফায়েড কিউরেটেড চ্যানেল লিস্ট
│   │
│   ├── fourkhdhub/             # 4KHDHub মিরর স্ক্র্যাপার
│   │   └── __init__.py
│   │
│   └── bdix/                   # BDIX ইন্টারফেস
│       └── __init__.py
│
├── player/                     # ভিডিও প্লেয়ার ও ডাউনলোডার
│   ├── __init__.py             # প্লেয়ার ডিটেকশন ও লঞ্চার
│   ├── base.py                 # BasePlayer ইন্টারফেস
│   ├── mpv.py                  # MPV লঞ্চার (হেডার ও সাবটাইটেল সহ)
│   ├── vlc.py                  # VLC লঞ্চার
│   └── downloader.py           # Rich প্রগ্রেস বার সহ ডাউনলোড ম্যানেজার
│
├── tui/                        # ইন্টারেক্টিভ টার্মিনাল ইউজার ইন্টারফেস
│   ├── __init__.py
│   ├── app.py                  # Rich-চালিত ফুল TUI অ্যাপ
│   └── banner.py               # ASCII আর্ট ও ব্যানার
│
├── cli/                        # কমান্ড লাইন আর্গুমেন্ট পার্সার
│   ├── __init__.py
│   └── parser.py
│
└── tests/                      # অটোমেটেড ইউনিট ও ইন্টিগ্রেশন টেস্ট
    ├── __init__.py
    └── test_providers.py
```

---

## 🚀 ইনস্টলেশন ও রান করার নিয়ম (How to Run)

### ১. ডিপেন্ডেন্সি ইনস্টল করুন:
```bash
pip install -r requirements.txt
```

### ২. ইন্টারেক্টিভ টার্মিনাল TUI চালু করুন:
```bash
python3 main.py
# অথবা
python3 main.py tui
```

### ৩. সরাসরি CLI কমান্ড ব্যবহার করুন:
```bash
# ১. যেকোনো মুভি বা সিরিজ সার্চ করুন:
python3 main.py search "Inception"
python3 main.py search "Breaking Bad"

# ২. মিডিয়া আইডি দিয়ে বিস্তারিত ও সিজন দেখুন:
python3 main.py details 6391474290696802080

# ৩. স্ট্রিম লিংক ও কোয়ালিটি রেজোলিউশন দেখুন:
python3 main.py streams 6391474290696802080

# ৪. সরাসরি প্লেয়ারে চালান:
python3 main.py play 6391474290696802080 --player mpv

# ৫. লাইভ আইপিটিভি চ্যানেল ব্রাউজ করুন:
python3 main.py tv
python3 main.py tv --category Sports
python3 main.py tv --category Bangla

# ৬. প্রোভাইডার লিস্ট দেখুন:
python3 main.py providers
```

---

## 🛠️ নতুন প্রোভাইডার যুক্ত করার নিয়ম (How to Add a New Provider)

নতুন যেকোনো ওয়েবসাইট বা স্ট্রিম সোর্স যুক্ত করার জন্য:

১. `providers/` ফোল্ডারে একটি নতুন ডিরেক্টরি তৈরি করুন (যেমন: `providers/myprovider/`)।
২. `BaseProvider` ক্লাসটি ইনহেরিট করে ইমপ্লিমেন্ট করুন:
```python
from providers.base import BaseProvider
from models.media import CatalogItem, MediaDetails
from models.release import Release

class MyProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "myprovider"

    @property
    def label(self) -> str:
        return "My Custom Provider"

    def search(self, query: str, page: int = 1) -> list[CatalogItem]:
        # আপনার সার্চ লজিক
        pass

    def get_details(self, media_id: str) -> MediaDetails:
        # মেটাডাটা ও ডিটেইলস
        pass

    def get_streams(self, media_id: str, season: int = 0, episode: int = 0) -> list[Release]:
        # স্ট্রিম লিংক রিটার্ন করুন
        pass
```
৩. `providers/__init__.py`-তে আপনার প্রোভাইডার ক্লাস রেজিস্টার করে দিন।
