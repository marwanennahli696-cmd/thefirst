import json
from datetime import datetime
import mysql.connector
from typing import Any, Dict, List, Optional

import config
from logger import get_logger

log = get_logger()


def _connect():
    try:
        return mysql.connector.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASS,
            database=config.MYSQL_DB,
        )
    except mysql.connector.Error as e:
        log.error(f"Connection error: {e}")
        return None


def _close(cursor, conn):
    try:
        if cursor: cursor.close()
    except Exception:
        pass
    try:
        if conn: conn.close()
    except Exception:
        pass


def _row_to_city(row):
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "subtitle": row[2] or "",
        "description": row[3] or "",
        "image": row[4] or "",
        "map_url": row[5] or "",
        "accent": json.loads(row[6]) if row[6] else [82, 116, 158],
        "stats": {
            "population": row[7] or "",
            "language": row[8] or "",
            "currency": row[9] or "MAD",
            "climate": row[10] or "",
        },
        "location": {
            "lat": row[11] or 0,
            "lng": row[12] or 0,
        },
        "restaurants": json.loads(row[13]) if row[13] else [],
        "hotels": json.loads(row[14]) if row[14] else [],
        "transports": json.loads(row[15]) if row[15] else [],
        "places": json.loads(row[16]) if row[16] else [],
    }


def get_all_cities() -> List[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return []
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities")
        rows = cursor.fetchall()
        return [_row_to_city(r) for r in rows]
    except mysql.connector.Error as e:
        log.error(f"get_all_cities error: {e}")
        return []
    finally:
        _close(cursor, conn)


def get_city(city_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE id = %s", (city_id,))
        row = cursor.fetchone()
        return _row_to_city(row)
    except mysql.connector.Error as e:
        log.error(f"get_city error: {e}")
        return None
    finally:
        _close(cursor, conn)


def save_city(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE id = %s", (data["id"],))
        exists = cursor.fetchone()
        stats = data.get("stats", {})
        loc = data.get("location", {})
        accent = json.dumps(data.get("accent", [82, 116, 158]))
        restaurants = json.dumps(data.get("restaurants", []))
        hotels = json.dumps(data.get("hotels", []))
        transports = json.dumps(data.get("transports", []))
        places = json.dumps(data.get("places", []))
        if exists:
            cursor.execute("""
                UPDATE cities SET
                    name=%s, subtitle=%s, description=%s, image=%s, map_url=%s,
                    accent=%s, population=%s, language=%s, currency=%s, climate=%s,
                    lat=%s, lng=%s, restaurants=%s, hotels=%s, transports=%s, places=%s
                WHERE id=%s
            """, (
                data["name"], data.get("subtitle",""), data.get("description",""),
                data.get("image",""), data.get("map_url",""),
                accent, stats.get("population",""), stats.get("language",""),
                stats.get("currency","MAD"), stats.get("climate",""),
                loc.get("lat",0), loc.get("lng",0),
                restaurants, hotels, transports, places,
                data["id"],
            ))
        else:
            cursor.execute("""
                INSERT INTO cities (id, name, subtitle, description, image, map_url,
                    accent, population, language, currency, climate,
                    lat, lng, restaurants, hotels, transports, places)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["id"], data["name"], data.get("subtitle",""),
                data.get("description",""), data.get("image",""), data.get("map_url",""),
                accent, stats.get("population",""), stats.get("language",""),
                stats.get("currency","MAD"), stats.get("climate",""),
                loc.get("lat",0), loc.get("lng",0),
                restaurants, hotels, transports, places,
            ))
        conn.commit()
        return data
    except mysql.connector.Error as e:
        log.error(f"save_city error: {e}")
        return None
    finally:
        _close(cursor, conn)


def delete_city(city_id: str) -> bool:
    conn = _connect()
    if not conn:
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cities WHERE id = %s", (city_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except mysql.connector.Error as e:
        log.error(f"delete_city error: {e}")
        return False
    finally:
        _close(cursor, conn)


def add_item(city_id: str, section: str, item: Dict[str, Any]) -> Optional[Dict]:
    city = get_city(city_id)
    if not city:
        return None
    items = city.setdefault(section, [])
    items.append(item)
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
        conn.commit()
        return item
    except mysql.connector.Error as e:
        log.error(f"add_item error: {e}")
        return None
    finally:
        _close(cursor, conn)


def update_item(city_id: str, section: str, idx: int, item: Dict) -> Optional[Dict]:
    city = get_city(city_id)
    if not city:
        return None
    items = city.get(section, [])
    if 0 <= idx < len(items):
        items[idx] = item
        conn = _connect()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
            conn.commit()
            return item
        except mysql.connector.Error as e:
            log.error(f"update_item error: {e}")
            return None
        finally:
            _close(cursor, conn)
    return None


def delete_item(city_id: str, section: str, idx: int) -> bool:
    city = get_city(city_id)
    if not city:
        return False
    items = city.get(section, [])
    if 0 <= idx < len(items):
        items.pop(idx)
        conn = _connect()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
            conn.commit()
            return True
        except mysql.connector.Error as e:
            log.error(f"delete_item error: {e}")
            return False
        finally:
            _close(cursor, conn)
    return False


def add_reservation(res):
    conn = _connect()
    if not conn:
        res["id"] = 0
        res["status"] = "pending"
        return res
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reservations (name, email, phone, birthdate,
                city_id, city_name, category, item_name, date_res,
                nights, persons, total, menu_items, created_at, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            res.get("name",""), res.get("email",""),
            res.get("phone",""), res.get("birthdate",""),
            res.get("city_id",""), res.get("city_name",""),
            res.get("category",""), res.get("item_name",""),
            res.get("date_res",""), res.get("nights",""), res.get("persons",""),
            res.get("total",""), json.dumps(res.get("menu_items","")),
            res.get("created_at",""), "pending",
        ))
        res_id = cursor.lastrowid
        conn.commit()
        res["id"] = res_id
        res["status"] = "pending"
        return res
    except mysql.connector.Error as e:
        log.error(f"add_reservation error: {e}")
        res["id"] = 0
        res["status"] = "pending"
        return res
    finally:
        _close(cursor, conn)


def get_reservations(status=None):
    conn = _connect()
    if not conn:
        return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        if status:
            cursor.execute("SELECT * FROM reservations WHERE status = %s ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM reservations ORDER BY id DESC")
        rows = cursor.fetchall()
        for r in rows:
            if r.get("menu_items") and isinstance(r["menu_items"], str):
                try:
                    r["menu_items"] = json.loads(r["menu_items"])
                except:
                    pass
        return rows
    except mysql.connector.Error as e:
        log.error(f"get_reservations error: {e}")
        return []
    finally:
        _close(cursor, conn)


def get_reservation(res_id):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reservations WHERE id = %s", (res_id,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        log.error(f"get_reservation error: {e}")
        return None
    finally:
        _close(cursor, conn)


def add_user(data):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""INSERT INTO users (first_name, last_name, email, country, phone, birthdate, password, created_at)
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                       (data["first_name"], data["last_name"], data["email"],
                        data["country"], data.get("phone",""), data.get("birthdate",""),
                        data["password"], datetime.now().isoformat()))
        conn.commit()
        return {"id": cursor.lastrowid}
    except mysql.connector.Error as e:
        log.error(f"add_user error: {e}")
        raise
    finally:
        _close(cursor, conn)


def get_user_by_email(email):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        log.error(f"get_user_by_email error: {e}")
        return None
    finally:
        _close(cursor, conn)


def update_reservation_status(res_id, status):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reservations WHERE id = %s", (res_id,))
        r = cursor.fetchone()
        if r:
            cursor.execute("UPDATE reservations SET status = %s WHERE id = %s", (status, res_id))
            conn.commit()
        return r
    except mysql.connector.Error as e:
        log.error(f"update_reservation_status error: {e}")
        return None
    finally:
        _close(cursor, conn)
