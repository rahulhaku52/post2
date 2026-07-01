import os
import json
import requests
import base64
import time
from io import BytesIO

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
A1ART_API_KEY = os.environ.get('A1ART_API_KEY')  # a1.art API Key

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ BOT_TOKEN or CHANNEL_ID not set!")
    exit(1)

if not A1ART_API_KEY:
    print("⚠️ A1ART_API_KEY not set — images will NOT be generated!")

INDEX_FILE = "last_index.json"

# পোস্ট লোড
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

total = len(posts)
print(f"📊 Total posts: {total}")

if total == 0:
    print("❌ No posts!")
    exit(1)

# last_index পড়া
try:
    with open(INDEX_FILE, 'r') as f:
        last_index = json.load(f)
    print(f"📂 Read last_index: {last_index}")
except:
    last_index = total
    print(f"📂 No file. Start from end. Set: {total}")

# শেষ থেকে শুরু
next_index = (last_index - 1) % total
print(f"➡️ Next index: {next_index} (0-{total-1})")

# পোস্ট
post = posts[next_index]
text = post.get('text', '')
print(f"📝 Post: {text[:60]}...")

# ========== a1.art দিয়ে ছবি বানানো ==========
def generate_image_from_text(text):
    """a1.art API দিয়ে টেক্সট থেকে ছবি জেনারেট করা"""
    if not A1ART_API_KEY:
        print("⚠️ No API key — skipping image generation.")
        return None

    # টেক্সট থেকে কিওয়ার্ড বের করে prompt তৈরি
    prompt = (
        "A beautiful Bangladeshi woman in a traditional saree, "
        "sensual pose, village background, moody lighting, "
        "cinematic, photorealistic, adult vibe, "
        "no nudity, tasteful, aesthetic"
    )
    # কনটেন্ট থেকে কিছু ইঙ্গিত নেওয়া
    if "শাড়ি" in text or "sari" in text.lower():
        prompt += ", blouse, saree fall, navel visible"
    if "ব্লাউজ" in text or "blouse" in text.lower():
        prompt += ", tight blouse, cleavage hint"
    if "প্যান্টি" in text or "panty" in text.lower():
        prompt += ", panty line visible through thin saree"
    if "গুদ" in text or "pussy" in text.lower():
        prompt += ", wet patch hint on saree"

    # a1.art API call
    url = "https://a1.art/api/v1/generate"
    headers = {
        "Authorization": f"Bearer {A1ART_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "negative_prompt": "nude, naked, explicit, porn, deformed, ugly",
        "width": 512,
        "height": 768,
        "steps": 25,
        "cfg_scale": 7,
        "sampler": "Euler a"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # সাধারণত API রিটার্ন করে image URL বা base64
            if "image_url" in data:
                return data["image_url"]
            elif "image" in data:  # base64 string
                return base64.b64decode(data["image"])
            else:
                print(f"⚠️ Unexpected response: {data}")
                return None
        else:
            print(f"❌ a1.art API error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

# ছবি বানাও (পাঠানোর আগে)
image_result = None
if A1ART_API_KEY:
    print("🎨 Generating image with a1.art...")
    image_result = generate_image_from_text(text)
    if image_result:
        print("✅ Image generated!")
    else:
        print("⚠️ Image generation failed — sending text only.")

# ইনলাইন বাটন
reply_markup = {
    "inline_keyboard": [
        [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}]
    ]
}

# ========== টেলিগ্রামে পাঠানো ==========
base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

if image_result and isinstance(image_result, str):  # URL হলে
    # photo URL হিসেবে পাঠাই
    res = requests.post(f"{base_url}/sendPhoto", json={
        "chat_id": CHANNEL_ID,
        "photo": image_result,
        "caption": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }, timeout=20).json()
    if res.get('ok'):
        print("✅ Photo (URL) + caption posted!")
    else:
        print(f"❌ Photo send error: {res}")
        # fallback: text only
        res = requests.post(f"{base_url}/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup
        }, timeout=15).json()
        if res.get('ok'):
            print("✅ Text fallback posted!")
        else:
            print(f"❌ Text fallback error: {res}")
            exit(1)

elif image_result and isinstance(image_result, bytes):  # base64 bytes হলে
    # মাল্টিপার্ট ফর্ম দিয়ে photo পাঠাই
    files = {"photo": ("image.png", BytesIO(image_result), "image/png")}
    data = {
        "chat_id": CHANNEL_ID,
        "caption": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(reply_markup)
    }
    res = requests.post(f"{base_url}/sendPhoto", data=data, files=files, timeout=20).json()
    if res.get('ok'):
        print("✅ Photo (bytes) + caption posted!")
    else:
        print(f"❌ Photo bytes send error: {res}")
        # fallback text
        res = requests.post(f"{base_url}/sendMessage", json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup
        }, timeout=15).json()
        if res.get('ok'):
            print("✅ Text fallback posted!")
        else:
            print(f"❌ Text fallback error: {res}")
            exit(1)

else:
    # no image — text only
    res = requests.post(f"{base_url}/sendMessage", json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
    }, timeout=15).json()
    if res.get('ok'):
        print("✅ Text posted!")
    else:
        print(f"❌ Telegram error: {res}")
        exit(1)

# সেভ index
with open(INDEX_FILE, 'w') as f:
    json.dump(next_index, f)
print(f"💾 Saved index: {next_index}")
