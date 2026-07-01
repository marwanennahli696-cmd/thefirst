import os
import sys
import json
import smtplib

import re
import urllib.parse
from email.mime.text import MIMEText
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, send_file, abort, request, session, redirect
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash

import database
import config
import translations
from logger import get_logger, get_audit

log = get_logger()
audit = get_audit()

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = config.FLASK_SECRET_KEY
app.config["SESSION_PERMANENT"] = False


@app.before_request
def log_request():
    path = request.path
    if path.startswith("/static") or path.startswith("/assets"):
        return
    log.info(f"{request.method} {path}")


def get_lang():
    return session.get("lang", "fr")


def translate(key, **kwargs):
    lang = get_lang()
    t = translations.TRANSLATIONS.get(lang, translations.TRANSLATIONS["fr"])
    val = t.get(key)
    if val is None:
        val = translations.TRANSLATIONS["fr"].get(key, key)
    if kwargs:
        val = val.format(**kwargs)
    return Markup(val) if "&" in str(val) else val


def translate_city(city, lang):
    if not city:
        return city
    cid = city.get("id", "")
    ct = translations.CITY_TRANSLATIONS.get(cid, {})
    lang_data = ct.get(lang, {}) if lang != "fr" else {}
    city = dict(city)
    city["name"] = lang_data.get("name", city.get("name", ""))
    city["subtitle"] = lang_data.get("subtitle", city.get("subtitle", ""))
    city["description"] = lang_data.get("description", city.get("description", ""))
    it = translations.ITEM_TRANSLATIONS.get(lang, {})
    for section in ("restaurants", "hotels", "transports", "places"):
        items = city.get(section, [])
        if not items:
            continue
        new_items = []
        for item in items:
            item = dict(item)
            note = item.get("note", "")
            if note in it:
                item["note"] = it[note]
            elif lang == "ar" and note in translations.ITEM_TRANSLATIONS.get("ar", {}):
                item["note"] = translations.ITEM_TRANSLATIONS["ar"][note]
            new_items.append(item)
        city[section] = new_items
    return city


@app.template_filter("img")
def img_url(path):
    if not path:
        return ""
    path = path.replace("\\", "/")
    if path.startswith("/"):
        return path
    return "/" + path


@app.context_processor
def inject_translations():
    lang = get_lang()
    return dict(_=translate, lang=lang, dir_="rtl" if lang == "ar" else "ltr")


@app.route("/")
def index():
    if "user" not in session:
        return render_template("signup.html")
    lang = get_lang()
    cities = database.get_all_cities()
    cities = [translate_city(c, lang) for c in cities]
    return render_template("index.html", cities=cities, user=session["user"])



@app.route("/signup")
def signup():
    if "user" in session:
        return redirect("/")
    return render_template("signup.html", error=request.args.get("error"), show_login=False)

@app.route("/signin", methods=["POST"])
def signin():
    email = request.form["email"]
    password = request.form.get("password", "")
    form_type = request.form.get("form", "signup")
    
    if form_type == "login":
        existing = database.get_user_by_email(email)
        
        if not existing:
            return render_template("signup.html", error=translate("err_email_not_found"), show_login=True)
        if not check_password_hash(existing["password"], password):
            audit.warning(f"FAILED LOGIN | {email}")
            return render_template("signup.html", error=translate("login_err_password"), show_login=True)
        audit.info(f"LOGIN | {email}")
        session["user"] = existing
        return redirect("/")

    # --- signup validation ---
    first = request.form.get("first_name", "")
    last = request.form.get("last_name", "")
    country = request.form.get("country", "")
    phone = request.form.get("phone", "")
    bd = request.form.get("birthdate", "")

    if re.search(r"\d", first):
        return render_template("signup.html", error=translate("err_prenom_numbers"), show_login=False)
    if re.search(r"\d", last):
        return render_template("signup.html", error=translate("err_nom_numbers"), show_login=False)
    if re.search(r"\d", country):
        return render_template("signup.html", error=translate("err_pays_numbers"), show_login=False)
    if phone and re.search(r"[A-Za-z]", phone):
        return render_template("signup.html", error=translate("err_phone_letters"), show_login=False)

    if bd:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", bd):
            return redirect("/signup")
        try:
            year = int(bd[:4])
            if year < 1960:
                return render_template("signup.html", error=translate("err_birthdate_year_old"), show_login=False)
            if year > 2026:
                return render_template("signup.html", error=translate("err_birthdate_year_future"), show_login=False)
        except ValueError:
            return redirect("/signup")

    existing = database.get_user_by_email(email)
    if existing:
        return render_template("signup.html", error=translate("signup_err_exists"), show_login=True)
    
    user_data = {
        "first_name": first,
        "last_name": last,
        "email": email,
        "country": country,
        "phone": phone,
        "birthdate": bd,
        "password": generate_password_hash(password),
    }
    saved = database.add_user(user_data)
    if not saved:
        audit.warning(f"REGISTER FAILED (duplicate) | {email}")
        return render_template("signup.html", error=translate("signup_err_exists"), show_login=True)
    audit.info(f"REGISTER | {email}")
    user_data["id"] = saved.get("id")
    session["user"] = user_data
    return redirect("/")

@app.route("/logout")
def signout():
    session.pop("user", None)
    return redirect("/signup")


@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in ("fr", "en", "ar"):
        session["lang"] = lang
    return redirect(request.referrer or "/")


@app.route("/city/<city_id>")
def city_detail(city_id):
    if "user" not in session:
        return render_template("signup.html")
    lang = get_lang()
    city = database.get_city(city_id)
    if not city:
        cities = database.get_all_cities()
        cities = [translate_city(c, lang) for c in cities]
        return render_template("index.html", cities=cities, error=translate("ville_introuvable"), user=session.get("user"))
    city = translate_city(city, lang)
    return render_template("city.html", city=city, user=session.get("user"))


@app.route("/api/cities")
def api_cities():
    if "user" not in session:
        return jsonify({"error": "not logged in"}), 401
    return jsonify(database.get_all_cities())


@app.route("/api/city/<city_id>")
def api_city(city_id):
    c = database.get_city(city_id)
    if not c:
        return jsonify({"error": "not found"}), 404
    return jsonify(c)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    msg = request.json.get("message", "").lower()
    lang = request.json.get("lang", "fr")
    cities = database.get_all_cities()

    rest_kw = ["restaurant", "manger", "eat", "مطعم", "أكل"]
    hotel_kw = ["hôtel", "hotel", "dormir", "sleep", "فندق", "نوم"]
    trans_kw = ["transport", "bus", "train", "مواصلات", "حافلة", "قطار"]
    place_kw = ["visit", "voir", "lieu", "place", "visiter", "see", "زيارة", "مكان", "رؤية"]

    for c in cities:
        cname = c["name"].lower()
        cname_ar = translations.CITY_TRANSLATIONS.get(c["id"], {}).get("ar", {}).get("name", "").lower()
        if cname in msg or (cname_ar and cname_ar in msg):
            name = translate_city(dict(c), lang)["name"]
            parts = []
            if any(k in msg for k in rest_kw):
                parts.append(("chat_restaurants", c.get("restaurants", [])))
            if any(k in msg for k in hotel_kw):
                parts.append(("chat_hotels", c.get("hotels", [])))
            if any(k in msg for k in trans_kw):
                parts.append(("chat_transports", c.get("transports", [])))
            if any(k in msg for k in place_kw):
                parts.append(("chat_lieux", c.get("places", [])))
            if not parts:
                desc = translate_city(dict(c), lang).get("description", "")
                return jsonify({"reply": f"{name} — {desc}"})
            replies = []
            for label_key, items in parts:
                label = translate(label_key, name=name)
                names = [i["name"] for i in items]
                if names:
                    replies.append(label + ", ".join(names))
            if not replies:
                replies.append(translate_city(dict(c), lang).get("description", ""))
            return jsonify({"reply": "\n\n".join(replies)})
    return jsonify({"reply": translate("chat_fallback")})

def send_email(to_email, subject, body, html=False):
    if not config.SMTP_USER or not config.SMTP_PASS:
        return False, "SMTP_USER ou SMTP_PASS vide"
    try:
        subtype = "html" if html else "plain"
        msg = MIMEText(str(body), subtype, "utf-8")
        msg["From"] = config.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg["Message-ID"] = "<{:.0f}@touristique-guide>".format(datetime.now().timestamp() * 1000)
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.sendmail(config.SMTP_FROM, [to_email], msg.as_string().encode("utf-8"))
        server.quit()
        return True, "OK"
    except Exception as e:
        return False, str(e)


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.json
    if data and data.get("username") == config.ADMIN_USER and data.get("password") == config.ADMIN_PASS:
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == config.ADMIN_USER and request.form.get("password") == config.ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin/dashboard")
        return render_template("admin_login.html", error=translate("admin_login_error"))
    if session.get("admin"):
        return redirect("/admin/dashboard")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")
    reservations = database.get_reservations()
    for r in reservations:
        items = r.get("menu_items", "")
        if isinstance(items, str) and items:
            try:
                items = json.loads(items)
            except Exception:
                items = []
        if isinstance(items, list):
            r["menu_display"] = ", ".join(["{} x{}".format(m.get("key",""), m.get("qty","")) for m in items])
        else:
            r["menu_display"] = ""
    msg = request.args.get("msg", "")
    return render_template("admin_dashboard.html", reservations=reservations, msg=msg)


@app.route("/admin/test-email")
def admin_test_email():
    if not session.get("admin"):
        return redirect("/admin")
    ok, err = send_email(config.SMTP_USER, "Test Email", "Ceci est un email de test depuis Guide Touristique.")
    if ok:
        return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Test email envoyé à " + config.SMTP_USER))
    else:
        return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Test ÉCHEC: " + err))

@app.route("/admin/accept/<int:res_id>")
def admin_accept(res_id):
    if not session.get("admin"):
        return redirect("/admin")
    r = database.update_reservation_status(res_id, "accepted")
    if r:
        audit.info(f"ACCEPT RESERVATION | {res_id} | {r.get('item_name','')} ({r.get('category','')}) by {r.get('name','')}")
        menu = r.get("menu_items","")
        if menu:
            try: menu = json.loads(menu); menu = "\n".join(["- {} x {}".format(m.get("key",""), m.get("qty","")) for m in menu])
            except Exception: pass
        pay_link = config.SITE_URL + "/paiement/" + str(r.get("id",""))
        body_html = translate("email_body_accepted", name=r.get("name",""), item=r.get("item_name",""),
                         category=r.get("category",""), city=r.get("city_name",""),
                         checkin=r.get("date_res",""), checkout=r.get("nights",""),
                         guests=str(r.get("persons","")), menu_items=menu,
                         payment_link=pay_link)
        subject = translate("email_subject_accepted")
        ok, err = send_email(r.get("email",""), subject, body_html, html=True)
        if ok:
            return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Email envoyé à " + r.get("email","")))
        else:
            return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Email ÉCHEC: " + err))
    return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Réservation acceptée"))


@app.route("/admin/refuse/<int:res_id>")
def admin_refuse(res_id):
    if not session.get("admin"):
        return redirect("/admin")
    r = database.update_reservation_status(res_id, "refused")
    if r:
        audit.info(f"REFUSE RESERVATION | {res_id} | {r.get('item_name','')} ({r.get('category','')}) by {r.get('name','')}")
        body = translate("email_body_refused", name=r.get("name",""), item=r.get("item_name",""),
                         category=r.get("category",""), city=r.get("city_name",""),
                         checkin=r.get("date_res",""), guests=str(r.get("persons","")))
        subject = translate("email_subject_refused")
        ok, err = send_email(r.get("email",""), subject, body)
        if ok:
            return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Email envoyé à " + r.get("email","")))
        else:
            return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Email ÉCHEC: " + err))
    return redirect("/admin/dashboard?msg=" + urllib.parse.quote("Réservation refusée"))



@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


@app.route("/admin/cities")
def admin_cities():
    if not session.get("admin"):
        return redirect("/admin")
    cities = database.get_all_cities()
    msg = request.args.get("msg", "")
    return render_template("admin_cities.html", cities=cities, msg=msg)


@app.route("/admin/cities/save", methods=["POST"])
def admin_city_save():
    if not session.get("admin"):
        return redirect("/admin")
    data = {
        "id": request.form["id"],
        "name": request.form["name"],
        "subtitle": request.form.get("subtitle", ""),
        "description": request.form.get("description", ""),
        "image": request.form.get("image", ""),
        "map_url": request.form.get("map_url", ""),
        "accent": [82, 116, 158],
        "stats": {
            "population": request.form.get("population", ""),
            "language": request.form.get("language", ""),
            "currency": request.form.get("currency", "MAD"),
            "climate": request.form.get("climate", ""),
        },
        "location": {
            "lat": float(request.form.get("lat", 0) or 0),
            "lng": float(request.form.get("lng", 0) or 0),
        },
        "restaurants": [],
        "hotels": [],
        "transports": [],
        "places": [],
    }
    orig = request.form.get("original_id", "")
    if orig and orig != data["id"]:
        database.delete_city(orig)
    existing = database.get_city(data["id"])
    if existing:
        data["restaurants"] = existing.get("restaurants", [])
        data["hotels"] = existing.get("hotels", [])
        data["transports"] = existing.get("transports", [])
        data["places"] = existing.get("places", [])
    database.save_city(data)
    return redirect("/admin/cities?msg=Ville enregistr%C3%A9e")


@app.route("/admin/cities/delete/<city_id>", methods=["POST"])
def admin_city_delete(city_id):
    if not session.get("admin"):
        return redirect("/admin")
    database.delete_city(city_id)
    return redirect("/admin/cities?msg=Ville supprim%C3%A9e")


@app.route("/admin/cities/<city_id>/add_item/<section>", methods=["POST"])
def admin_add_item(city_id, section):
    if not session.get("admin"):
        return redirect("/admin")
    item = {
        "name": request.form["name"],
        "image": request.form.get("image", ""),
        "note": request.form.get("note", ""),
    }
    stars = request.form.get("stars", "")
    if stars:
        item["stars"] = int(stars)
    database.add_item(city_id, section, item)
    return redirect("/admin/cities?msg=%C3%89l%C3%A9ment+ajout%C3%A9")


@app.route("/admin/cities/<city_id>/update_item/<section>/<int:idx>", methods=["POST"])
def admin_update_item(city_id, section, idx):
    if not session.get("admin"):
        return redirect("/admin")
    item = {
        "name": request.form["name"],
        "image": request.form.get("image", ""),
        "note": request.form.get("note", ""),
    }
    stars = request.form.get("stars", "")
    if stars:
        item["stars"] = int(stars)
    database.update_item(city_id, section, idx, item)
    return redirect("/admin/cities?msg=%C3%89l%C3%A9ment+modifi%C3%A9")


@app.route("/admin/cities/<city_id>/delete_item/<section>/<int:idx>", methods=["POST"])
def admin_delete_item(city_id, section, idx):
    if not session.get("admin"):
        return redirect("/admin")
    database.delete_item(city_id, section, idx)
    return redirect("/admin/cities?msg=%C3%89l%C3%A9ment+supprim%C3%A9")


@app.route("/api/reserve", methods=["POST"])
def api_reserve():
    if "user" not in session:
        return jsonify({"error": "not logged in"}), 401
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400
    bd = data.get("birthdate", "")
    dr = data.get("date_res", "")
    if bd and not re.match(r"^\d{4}-\d{2}-\d{2}$", bd):
        return jsonify({"error": "invalid birthdate format"}), 400
    if dr and not re.match(r"^\d{4}-\d{2}-\d{2}$", dr):
        return jsonify({"error": "invalid date format"}), 400
    cat = data.get("category", "")
    if cat == "hotel":
        nights = data.get("nights", "")
        persons = data.get("persons", "")
        try:
            n = int(nights)
            p = int(persons)
        except (ValueError, TypeError):
            return jsonify({"error": "invalid nights or persons"}), 400
        if n < 1:
            return jsonify({"error": "nights must be at least 1"}), 400
        if p < 1:
            return jsonify({"error": "persons must be at least 1"}), 400
        if p == 1 and n >= 9:
            return jsonify({"error": "1 person cannot book 9 nights or more"}), 400
    elif cat == "restaurant":
        menu_str = data.get("menu_items", "")
        if not menu_str:
            return jsonify({"error": "no menu items selected"}), 400
        try:
            items = json.loads(menu_str)
            if not items or len(items) == 0:
                return jsonify({"error": "no menu items selected"}), 400
        except json.JSONDecodeError:
            return jsonify({"error": "invalid menu data"}), 400
    res = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "birthdate": bd,
        "city_id": data.get("city_id", ""),
        "city_name": data.get("city_name", ""),
        "category": data.get("category", ""),
        "item_name": data.get("item_name", ""),
        "date_res": dr,
        "nights": data.get("nights", ""),
        "persons": data.get("persons", ""),
        "total": data.get("total", ""),
        "menu_items": data.get("menu_items", ""),
        "created_at": datetime.now().isoformat(),
    }
    saved = database.add_reservation(res)
    audit.info(f"NEW RESERVATION | {saved.get('id')} | {data.get('item_name')} ({data.get('category')}) | {data.get('city_name')} | {data.get('email')}")
    return jsonify({"ok": True, "id": saved.get("id")})


@app.route("/paiement/<int:res_id>")
def paiement(res_id):
    r = database.get_reservation(res_id)
    if not r:
        abort(404)
    return render_template("payment.html", res=r)


@app.route("/assets/cities/<path:filename>")
def assets(filename):
    safe_path = os.path.normpath(os.path.join(config.ASSETS_DIR, filename))
    if not safe_path.startswith(os.path.normpath(config.ASSETS_DIR)):
        abort(403)
    if not os.path.exists(safe_path):
        abort(404)
    return send_file(safe_path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
