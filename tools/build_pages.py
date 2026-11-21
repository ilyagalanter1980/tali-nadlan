#!/usr/bin/env python3
"""Build static, search-friendly pages for every property in index.html.

Creates apt/<id>.html (Hebrew) and apt/<id>-ru.html (Russian), apt/index.html,
sitemap.xml and robots.txt, and adds Open Graph + JSON-LD to index.html.
Run from the repo root after every sync:  python3 tools/build_pages.py
"""
import html, json, os, re, datetime

SITE = "https://tali-nadlan.galanter-il.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

src = open("index.html", encoding="utf-8").read()
data = json.loads(re.search(r'id="data" data-keep>(.*?)</script>', src, re.S).group(1))
S = data["settings"]
PHONE = S.get("phone", "")
WA = "972" + re.sub(r"\D", "", PHONE).lstrip("0")
AGENT = S.get("agent", "טלי גלנטר")
BRAND = S.get("name", "טלי גלנטר נדל״ן")
LIC = S.get("license", "")
SOCIAL = [u for u in (S.get("fb"), S.get("ig"), S.get("tt")) if u]

T = {
    "he": dict(dir="rtl", lang="he", sale="למכירה", rent="להשכרה", sold="נמכר", rented="הושכר",
               types=dict(apartment="דירה", penthouse="פנטהאוז", duplex="דופלקס", house="בית פרטי"),
               feats=dict(parking="חניה", mamad="ממ״ד", balcony="מרפסת", storage="מחסן", ac="מיזוג",
                          accessible="נגישות", renovated="משופצת", view="נוף", elevator="מעלית"),
               rooms="חדרים", sqm="מ״ר", floor="קומה", ground="קומת קרקע", price="מחיר", onreq="מחיר לפי פנייה",
               month=" לחודש", call="להתקשר", wa="שליחת וואטסאפ", all="לכל הנכסים באתר", more="עוד נכסים",
               watext="שלום טלי, אני מתעניין/ת בנכס מס׳ {id}: {url}", ref="נכס מס׳", broker="מתווכת מקרקעין · רישיון תיווך מס׳",
               alltitle="כל הנכסים – " + BRAND, other="Русский", city_word="ב"),
    "ru": dict(dir="ltr", lang="ru", sale="Продажа", rent="Аренда", sold="Продано", rented="Сдано",
               types=dict(apartment="Квартира", penthouse="Пентхаус", duplex="Дуплекс", house="Частный дом"),
               feats=dict(parking="Парковка", mamad="Мамад (защищённая комната)", balcony="Балкон", storage="Кладовка",
                          ac="Кондиционеры", accessible="Доступность", renovated="Ремонт", view="Вид", elevator="Лифт"),
               rooms="комн.", sqm="м²", floor="Этаж", ground="Первый этаж", price="Цена", onreq="Цена по запросу",
               month=" в месяц", call="Позвонить", wa="Написать в WhatsApp", all="Все объекты на сайте", more="Другие объекты",
               watext="Здравствуйте, Тали! Меня интересует объект № {id}: {url}", ref="Объект №", broker="Риелтор · лицензия №",
               alltitle="Все объекты – Тали Галантер, недвижимость", other="עברית", city_word="в "),
}

def esc(x): return html.escape(str(x or ""), quote=True)

def tr(a, lang, k):
    if lang != "he":
        v = (a.get("tr") or {}).get(lang, {}).get(k)
        if v: return v
    return a.get(k) or ""

def photos(a):
    out = []
    for p in a.get("photos") or []:
        if p.startswith("assets/") and os.path.exists(p): out.append(p)
    return out

def videos(a):
    return [v for v in a.get("videos") or [] if v.startswith("assets/") and os.path.exists(v)]

def money(n): return f"{int(n):,}"

def title_of(a, lang):
    t = T[lang]
    deal = t["rent"] if a["deal"] == "rent" else t["sale"]
    typ = t["types"].get(a["type"], a["type"])
    parts = [f"{typ} {a['rooms']:g} {t['rooms']}" if a.get("rooms") else typ]
    loc = ", ".join(x for x in [tr(a, lang, "street"), tr(a, lang, "hood"), tr(a, lang, "city")] if x)
    return f"{deal}: {' '.join(parts)} – {loc}"

def status_txt(a, lang):
    if a.get("status") == "sold":
        return T[lang]["rented"] if a["deal"] == "rent" else T[lang]["sold"]
    return ""

def page_url(a, lang): return f"{SITE}/apt/{a['id']}{'' if lang == 'he' else '-' + lang}.html"

CSS = """
:root{--ink:#1C1917;--muted:#6B645C;--gold:#B48A3C;--bg:#FAF7F2;--card:#fff;--line:#E7E1D8;--sold:#9F1239;--wa:#15803D}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 Heebo,"IBM Plex Sans Hebrew",system-ui,sans-serif}
a{color:inherit}.wrap{max-width:980px;margin:0 auto;padding:0 18px}
header{border-bottom:1px solid var(--line);background:#fff}header .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px}
.brand{font-family:"Frank Ruhl Libre",serif;font-size:26px;font-weight:700;text-decoration:none}.brand small{display:block;font:500 12px Heebo,sans-serif;color:var(--muted);letter-spacing:.06em}
.lang{font-size:14px;color:var(--muted)}
h1{font-family:"Frank Ruhl Libre",serif;font-weight:500;font-size:clamp(26px,4.5vw,40px);line-height:1.2;margin:28px 0 8px}
.meta{display:flex;flex-wrap:wrap;gap:6px 18px;color:var(--muted);margin-bottom:6px}.meta b{color:var(--ink)}
.price{font-family:"Frank Ruhl Libre",serif;font-size:32px;margin:6px 0 18px}
.badge{display:inline-block;background:var(--sold);color:#fff;border-radius:4px;padding:4px 12px;font-weight:700;margin-inline-start:10px;font-size:15px;vertical-align:middle}
.is-sold .price{color:var(--sold);text-decoration:line-through}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:8px 0 22px}
.gallery img,.gallery video{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:8px;display:block;background:#eee}
.gallery .hero{grid-column:1/-1;aspect-ratio:16/9}.gallery video{aspect-ratio:9/16;max-height:520px}
.is-sold .gallery img{filter:grayscale(.85)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin-bottom:18px}
.desc{white-space:pre-line}.feats{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:0}
.feats li{border:1px solid var(--line);border-radius:999px;padding:4px 14px;background:#fff}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:12px 22px;border-radius:6px;text-decoration:none;font-weight:700;border:1px solid var(--ink)}
.btn.wa{background:var(--wa);border-color:var(--wa);color:#fff}.btn.ink{background:var(--ink);color:#fff}
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:18px 0 30px}
.item{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;text-decoration:none}
.item img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}.item div{padding:12px 14px}.item b{display:block}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px;padding:22px 0 40px;margin-top:20px}
.sticky{position:sticky;bottom:0;background:rgba(250,247,242,.96);border-top:1px solid var(--line);padding:10px 0;display:none}
@media(max-width:640px){.sticky{display:block}.sticky .cta{margin:0}.sticky .btn{flex:1}}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&family=Frank+Ruhl+Libre:wght@500;700&display=swap">'

def head(lang, title, desc, url, img, extra=""):
    t = T[lang]
    alt = ""
    return f"""<!doctype html><html lang="{t['lang']}" dir="{t['dir']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">{alt}
<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(BRAND)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(img)}">
<meta property="og:locale" content="{'he_IL' if lang=='he' else 'ru_RU'}"><meta name="twitter:card" content="summary_large_image">
{FONTS}<style>{CSS}</style>{extra}</head>"""

def header(lang, other_href):
    t = T[lang]
    return f"""<body><header><div class="wrap"><a class="brand" href="/">{esc(BRAND)}<small>{esc(t['broker'])} {esc(LIC)}</small></a>
<a class="lang" href="{esc(other_href)}">{t['other']}</a></div></header>"""

def footer(lang):
    t = T[lang]
    soc = " · ".join(f'<a href="{esc(u)}" rel="noopener" target="_blank">{n}</a>' for u, n in zip(SOCIAL, ["Facebook", "Instagram", "TikTok"]))
    return f"""<footer><div class="wrap"><b>{esc(AGENT)}</b> · {esc(t['broker'])} {esc(LIC)} · <a href="tel:{esc(PHONE)}">{esc(PHONE)}</a><br>{soc}</div></footer>"""

def apt_page(a, lang, others):
    t = T[lang]
    ph, vids = photos(a), videos(a)
    url = page_url(a, lang)
    img = f"{SITE}/{ph[0]}" if ph else HOME_IMG
    st = status_txt(a, lang)
    title = title_of(a, lang) + (f" ({st})" if st else "") + " | " + ("Тали Галантер" if lang == "ru" else BRAND)
    raw_desc = re.sub(r"\s+", " ", tr(a, lang, "desc")).strip()
    desc = raw_desc[:155] + ("…" if len(raw_desc) > 155 else "")
    city = tr(a, lang, "city")
    # JSON-LD
    ld = {"@context": "https://schema.org", "@type": "RealEstateListing", "name": title_of(a, lang), "url": url,
          "description": raw_desc[:500], "image": [f"{SITE}/{p}" for p in ph[:6]] or [HOME_IMG],
          "inLanguage": lang}
    c = str(a.get("created") or "")
    if len(c) == 8: ld["datePosted"] = f"{c[:4]}-{c[4:6]}-{c[6:]}"
    offer = {"@type": "Offer", "priceCurrency": "ILS",
             "availability": "https://schema.org/SoldOut" if a.get("status") == "sold" else "https://schema.org/InStock",
             "businessFunction": "http://purl.org/goodrelations/v1#LeaseOut" if a["deal"] == "rent" else "http://purl.org/goodrelations/v1#Sell",
             "seller": {"@type": "RealEstateAgent", "name": BRAND, "telephone": PHONE, "url": SITE + "/"}}
    if a.get("price"): offer["price"] = a["price"]
    ld["offers"] = offer
    item = {"@type": "SingleFamilyResidence" if a["type"] == "house" else "Apartment",
            "address": {"@type": "PostalAddress", "addressLocality": a.get("city", ""), "addressCountry": "IL"}}
    if a.get("street"): item["address"]["streetAddress"] = a["street"]
    if a.get("rooms"): item["numberOfRooms"] = a["rooms"]
    if a.get("size"): item["floorSize"] = {"@type": "QuantitativeValue", "value": a["size"], "unitCode": "MTK"}
    ld["about"] = item
    ldj = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    other = f"/apt/{a['id']}{'-ru' if lang == 'he' else ''}.html"
    h = head(lang, title, desc, url, img, ldj) + header(lang, other)
    h += f'<main class="wrap{" is-sold" if st else ""}">'
    h += f"<h1>{esc(title_of(a, lang))}{f'<span class=badge>{esc(st)}</span>' if st else ''}</h1>"
    meta = []
    if a.get("rooms"): meta.append(f"<span><b>{a['rooms']:g}</b> {t['rooms']}</span>")
    if a.get("size"): meta.append(f"<span><b>{a['size']}</b> {t['sqm']}</span>")
    if a.get("floor") is not None and a.get("type") != "house":
        meta.append(f"<span>{t['ground'] if not a.get('floor') else t['floor'] + ' ' + str(a['floor'])}</span>")
    meta.append(f"<span>{t['ref']} {a['id']}</span>")
    h += '<div class="meta">' + "".join(meta) + "</div>"
    pr = f"{money(a['price'])} ₪{t['month'] if a['deal']=='rent' else ''}" if a.get("price") else t["onreq"]
    h += f'<div class="price">{esc(pr)}</div>'
    if ph or vids:
        h += '<div class="gallery">'
        for i, p in enumerate(ph[:12]):
            h += f'<img src="/{esc(p)}" alt="{esc(title_of(a, lang))} – {i+1}"{" class=hero" if i == 0 else ""} loading="{"eager" if i == 0 else "lazy"}">'
        for v in vids:
            h += f'<video src="/{esc(v)}" controls playsinline preload="metadata"></video>'
        h += "</div>"
    walink = f"https://wa.me/{WA}?text=" + html.escape(re.sub(" ", "%20", t["watext"].format(id=a["id"], url=url)))
    cta = f'<div class="cta"><a class="btn wa" href="{walink}" target="_blank" rel="noopener">{t["wa"]}</a><a class="btn ink" href="tel:{esc(PHONE)}">{t["call"]} {esc(PHONE)}</a><a class="btn" href="/#apt-{a["id"]}">{t["all"]}</a></div>'
    if not st: h += cta
    h += f'<section class="card"><div class="desc">{esc(tr(a, lang, "desc"))}</div></section>'
    fs = [t["feats"].get(f, f) for f in a.get("features") or []]
    if fs: h += '<section class="card"><ul class="feats">' + "".join(f"<li>{esc(f)}</li>" for f in fs) + "</ul></section>"
    if others:
        h += f"<h2>{t['more']}</h2>" + listing(others, lang)
    h += "</main>"
    if not st: h += f'<div class="sticky"><div class="wrap">{cta}</div></div>'
    return h + footer(lang) + "</body></html>"

def listing(apts, lang):
    t = T[lang]
    out = '<div class="list">'
    for a in apts:
        ph = photos(a)
        st = status_txt(a, lang)
        im = f'<img src="/{esc(ph[0])}" alt="{esc(title_of(a, lang))}" loading="lazy">' if ph else ""
        pr = f"{money(a['price'])} ₪" if a.get("price") else t["onreq"]
        out += f'<a class="item" href="/apt/{a["id"]}{"" if lang == "he" else "-" + lang}.html">{im}<div><b>{esc(title_of(a, lang))}</b>{esc(st or pr)}</div></a>'
    return out + "</div>"

apts = [a for a in data["apts"] if a.get("status") in ("available", "sold", "exclusive")]
avail = [a for a in apts if a.get("status") != "sold"]
hero = next((a for a in avail if a.get("starred") and photos(a)), None) or next((a for a in avail if photos(a)), None)
HOME_IMG = f"{SITE}/{photos(hero)[0]}" if hero else ""

os.makedirs("apt", exist_ok=True)
for f in os.listdir("apt"):
    if f.endswith(".html"): os.remove(os.path.join("apt", f))
urls = [SITE + "/", SITE + "/apt/", SITE + "/apt/index-ru.html"]
for a in apts:
    for lang in ("he", "ru"):
        others = [o for o in avail if o["id"] != a["id"]][:6]
        open(f"apt/{a['id']}{'' if lang == 'he' else '-' + lang}.html", "w", encoding="utf-8").write(apt_page(a, lang, others))
        urls.append(page_url(a, lang))

for lang, fn in (("he", "index.html"), ("ru", "index-ru.html")):
    t = T[lang]
    ttl = t["alltitle"]
    d = ("כל הדירות והבתים למכירה ולהשכרה של טלי גלנטר נדל״ן באשדוד, גן יבנה, אשקלון והסביבה." if lang == "he"
         else "Квартиры и дома на продажу и в аренду в Ашдоде, Ган-Явне, Ашкелоне и окрестностях – Тали Галантер, недвижимость.")
    other = "/apt/index-ru.html" if lang == "he" else "/apt/"
    h = head(lang, ttl, d, SITE + ("/apt/" if lang == "he" else "/apt/index-ru.html"), HOME_IMG) + header(lang, other)
    h += f'<main class="wrap"><h1>{esc(ttl)}</h1>{listing(avail + [a for a in apts if a.get("status") == "sold"], lang)}</main>'
    open("apt/" + fn, "w", encoding="utf-8").write(h + footer(lang) + "</body></html>")


# City pages: one page per city that has properties
CITY_SLUG = {"אשדוד": "ashdod", "גן יבנה": "gan-yavne", "אשקלון": "ashkelon"}
os.makedirs("area", exist_ok=True)
for f in os.listdir("area"):
    if f.endswith(".html"): os.remove(os.path.join("area", f))
for city, slug in CITY_SLUG.items():
    here = [a for a in avail if a.get("city") == city]
    if not here: continue
    sale = [a for a in here if a["deal"] != "rent"]; rent = [a for a in here if a["deal"] == "rent"]
    ttl = f"דירות ובתים למכירה ולהשכרה ב{city} | {BRAND}"
    d = f"נכסים עדכניים למכירה ולהשכרה ב{city} מבית {BRAND}: {len(sale)} למכירה, {len(rent)} להשכרה. ליווי אישי של מתווכת מוסמכת – {PHONE}."
    url = f"{SITE}/area/{slug}.html"
    hoods = sorted({a.get('hood') for a in here if a.get('hood')})
    h = head("he", ttl, d, url, HOME_IMG) + header("he", "/apt/index-ru.html")
    h += f'<main class="wrap"><h1>נכסים למכירה ולהשכרה ב{esc(city)}</h1>'
    h += f'<p>{esc(AGENT)}, מתווכת מקרקעין מוסמכת (רישיון {esc(LIC)}), מלווה קונים, מוכרים, שוכרים ומשכירים ב{esc(city)}' + (f" – בין היתר ב{esc(', '.join(hoods))}" if hoods else "") + f'. מחפשים נכס או רוצים למכור? <a href="tel:{esc(PHONE)}">{esc(PHONE)}</a></p>'
    if sale: h += "<h2>למכירה</h2>" + listing(sale, "he")
    if rent: h += "<h2>להשכרה</h2>" + listing(rent, "he")
    h += "</main>"
    open(f"area/{slug}.html", "w", encoding="utf-8").write(h + footer("he") + "</body></html>")
    urls.append(url)

today = datetime.date.today().isoformat()
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
open("sitemap.xml", "w").write(sm + "</urlset>\n")
open("robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

# Open Graph + structured data on the home page (idempotent)
src = re.sub(r"\n?<!-- seo:start -->.*?<!-- seo:end -->", "", src, flags=re.S)
home_desc = "טלי גלנטר נדל״ן – דירות ובתים למכירה ולהשכרה באשדוד, גן יבנה, אשקלון והסביבה. ליווי אישי ומקצועי, מתווכת מוסמכת."
agent_ld = {"@context": "https://schema.org", "@type": "RealEstateAgent", "name": BRAND, "url": SITE + "/",
            "telephone": PHONE, "image": HOME_IMG, "areaServed": ["אשדוד", "גן יבנה", "אשקלון"], "sameAs": SOCIAL,
            "address": {"@type": "PostalAddress", "addressLocality": "אשדוד", "addressCountry": "IL"}}
block = ('\n<!-- seo:start -->'
         f'<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(BRAND)}">'
         f'<meta property="og:title" content="{esc(BRAND)} – דירות למכירה ולהשכרה באשדוד">'
         f'<meta property="og:description" content="{esc(home_desc)}"><meta property="og:url" content="{SITE}/">'
         f'<meta property="og:image" content="{esc(HOME_IMG)}"><meta property="og:locale" content="he_IL">'
         '<meta name="twitter:card" content="summary_large_image">'
         '<script type="application/ld+json">' + json.dumps(agent_ld, ensure_ascii=False) + '</script>'
         f'<noscript><a href="/apt/">כל הנכסים</a></noscript>'
         '<!-- seo:end -->')
src = src.replace('<link rel="canonical" href="https://tali-nadlan.galanter-il.com/">',
                  '<link rel="canonical" href="https://tali-nadlan.galanter-il.com/">' + block, 1)
open("index.html", "w", encoding="utf-8").write(src)
print(f"built {len(apts)*2} property pages, {len(urls)} sitemap urls; home image {HOME_IMG}")
