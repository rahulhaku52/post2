import os, json, requests, base64, time
from io import BytesIO
from urllib.parse import quote

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
A1ART_API_KEY = os.environ.get('A1ART_API_KEY')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ BOT_TOKEN or CHANNEL_ID not set!")
    exit(1)

INDEX_FILE = "last_index.json"

with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

total = len(posts)
print(f"📊 Total posts: {total}")
if total == 0: print("❌ No posts!"); exit(1)

try:
    with open(INDEX_FILE, 'r') as f: last_index = json.load(f)
    print(f"📂 Read last_index: {last_index}")
except:
    last_index = total
    print(f"📂 No file. Start from end. Set: {total}")

next_index = (last_index - 1) % total
print(f"➡️ Next index: {next_index} (0-{total-1})")

post = posts[next_index]
text = post.get('text', '')
print(f"📝 Post: {text[:60]}...")

# ===================== ইমেজ জেনারেশন =====================
def build_prompt(text):
    prompt = (
        "A beautiful Bangladeshi woman in a traditional saree, "
        "sensual pose, village background, moody lighting, "
        "cinematic, photorealistic, adult vibe, "
        "no nudity, tasteful, aesthetic"
    )
    if "শাড়ি" in text or "sari" in text.lower():
        prompt += ", blouse, saree fall, navel visible"
    if "ব্লাউজ" in text or "blouse" in text.lower():
        prompt += ", tight blouse, cleavage hint"
    if "প্যান্টি" in text or "panty" in text.lower():
        prompt += ", panty line visible through thin saree"
    if "গুদ" in text or "pussy" in text.lower():
        prompt += ", wet patch hint on saree"
    return prompt

def generate_with_a1art(prompt):
    """a1.art API - একাধিক এন্ডপয়েন্ট ট্রাই করবে"""
    if not A1ART_API_KEY: return None

    # প্রথমে api.a1.art, তারপর a1.art/api
    endpoints = [
        "https://api.a1.art/v1/generate",
        "https://a1.art/api/v1/generate",
        "https://api.a1.art/v1/images/generations"
    ]
    for url in endpoints:
        print(f"🎯 Trying a1.art: {url}")
        headers = {"Authorization": f"Bearer {A1ART_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "negative_prompt": "nude, naked, explicit, porn, deformed, ugly",
            "width": 512, "height": 768, "steps": 25, "cfg_scale": 7, "sampler": "Euler a"
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                # বিভিন্ন রেসপন্স ফরম্যাট
                for key in ["image_url", "url"]:
                    if key in data and data[key]:
                        return data[key]
                if "image" in data: return base64.b64decode(data["image"])
                if "data" in data and isinstance(data["data"], list) and data["data"]:
                    item = data["data"][0]
                    if "url" in item: return item["url"]
                    if "b64_json" in item: return base64.b64decode(item["b64_json"])
                    if "image" in item: return base64.b64decode(item["image"])
                print(f"   Unknown response: {str(data)[:200]}")
            else:
                print(f"   Response: {resp.text[:300]}")
        except Exception as e:
            print(f"   Error: {e}")
    return None

def generate_with_pollinations(prompt):
    """Pollinations.ai – ফ্রি, কোনো API Key লাগে না"""
    try:
        # prompt URL-encode করে সরাসরি GET
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        # ছবি ডাউনলোড
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 100:
            return BytesIO(resp.content).read()  # bytes
        else:
            print(f"   Pollinations failed: status {resp.status_code}, size {len(resp.content)}")
            return None
    except Exception as e:
        print(f"   Pollinations error: {e}")
        return None

# মূল লজিক
image_result = None
prompt = build_prompt(text)

# ১) a1.art চেষ্টা করো
if A1ART_API_KEY:
    print("🎨 Trying a1.art...")
    image_result = generate_with_a1art(prompt)
    if image_result: print("✅ a1.art success!")
    else: print("⚠️ a1.art failed, falling back to Pollinations...")

# ২) a1.art ব্যর্থ হলে Pollinations
if not image_result:
    print("🌐 Trying Pollinations.ai...")
    image_result = generate_with_pollinations(prompt)
    if image_result: print("✅ Pollinations success!")
    else: print("❌ All image generation failed, sending text only.")

# ===================== টেলিগ্রামে পাঠানো =====================
reply_markup = {"inline_keyboard": [[{"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}]]}
base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_fallback_text():
    return requests.post(f"{base_url}/sendMessage", json={
        "chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": True, "reply_markup": reply_markup
    }, timeout=15).json()

if image_result:
    # URL হলে sendPhoto
    if isinstance(image_result, str):
        res = requests.post(f"{base_url}/sendPhoto", json={
            "chat_id": CHANNEL_ID, "photo": image_result, "caption": text,
            "parse_mode": "HTML", "reply_markup": reply_markup
        }, timeout=20).json()
        if not res.get('ok'):
            print(f"❌ Photo (URL) error: {res}")
            res = send_fallback_text()
            print("✅ Fallback text sent" if res.get('ok') else f"❌ Text error: {res}")
        else: print("✅ Photo (URL) + caption posted!")
    else:  # bytes
        files = {"photo": ("image.png", BytesIO(image_result), "image/png")}
        data = {"chat_id": CHANNEL_ID, "caption": text, "parse_mode": "HTML", "reply_markup": json.dumps(reply_markup)}
        res = requests.post(f"{base_url}/sendPhoto", data=data, files=files, timeout=20).json()
        if not res.get('ok'):
            print(f"❌ Photo (bytes) error: {res}")
            res = send_fallback_text()
            print("✅ Fallback text sent" if res.get('ok') else f"❌ Text error: {res}")
        else: print("✅ Photo (bytes) + caption posted!")
else:
    res = send_fallback_text()
    print("✅ Text only posted" if res.get('ok') else f"❌ Text error: {res}")

# index save
with open(INDEX_FILE, 'w') as f:
    json.dump(next_index, f)
print(f"💾 Saved index: {next_index}")
