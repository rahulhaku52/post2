import os, json, requests, time
from io import BytesIO

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ BOT_TOKEN or CHANNEL_ID not set!")
    exit(1)

INDEX_FILE = "last_index.json"
REPLY_MARKUP = {
    "inline_keyboard": [
        [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}]
    ]
}

# ---------- পোস্ট লোড ----------
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

total = len(posts)
print(f"📊 Total posts: {total}")
if total == 0:
    print("❌ No posts!")
    exit(1)

# ---------- ইনডেক্স ----------
try:
    with open(INDEX_FILE, 'r') as f:
        last_index = json.load(f)
    print(f"📂 Read last_index: {last_index}")
except:
    last_index = total
    print(f"📂 No file. Start from end. Set: {total}")

next_index = (last_index - 1) % total
print(f"➡️ Next index: {next_index} (0-{total-1})")

post = posts[next_index]
caption = post.get('text', '')
print(f"📝 Caption: {caption[:60]}...")

# ---------- ইমেজ জেনারেশন (শুধু Pollinations) ----------
def build_image_prompt(text):
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
    # ছোটো করে নিচ্ছি যাতে URL বেশি লম্বা না হয়
    return prompt[:300]

def fetch_pollinations_image(prompt):
    encoded = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}"
    print(f"🎨 Pollinations URL: {url}")

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=60)
            print(f"   Attempt {attempt+1}: status {resp.status_code}, length {len(resp.content)}")
            if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
                return BytesIO(resp.content).read()  # bytes
            elif resp.status_code == 503:
                print(f"   Server busy, retrying in 8 sec...")
                time.sleep(8)
            else:
                print(f"   Unexpected status/content-type. Body: {resp.text[:100]}")
                break
        except Exception as e:
            print(f"   Error: {e}")
            break
    return None

print("🎨 Generating image with Pollinations...")
prompt = build_image_prompt(caption)
image_bytes = fetch_pollinations_image(prompt)

# ---------- টেলিগ্রামে পাঠানো ----------
send_photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
send_msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

if image_bytes:
    # ছবি পাঠাই
    files = {"photo": ("image.jpg", image_bytes, "image/jpeg")}
    data = {
        "chat_id": CHANNEL_ID,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(REPLY_MARKUP)
    }
    try:
        resp = requests.post(send_photo_url, files=files, data=data, timeout=30).json()
        if resp.get('ok'):
            print("✅ Image + caption posted!")
        else:
            print(f"❌ sendPhoto error: {resp}")
            # fallback টেক্সট
            resp2 = requests.post(send_msg_url, json={
                "chat_id": CHANNEL_ID,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": REPLY_MARKUP
            }, timeout=15).json()
            print("✅ Text fallback posted" if resp2.get('ok') else f"❌ Text fallback error: {resp2}")
    except Exception as e:
        print(f"❌ Exception sending photo: {e}")
        # fallback
        requests.post(send_msg_url, json={
            "chat_id": CHANNEL_ID,
            "text": caption,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": REPLY_MARKUP
        }, timeout=15)
else:
    # ছবি নেই – শুধু টেক্সট
    print("⚠️ Image generation failed – sending text only.")
    resp = requests.post(send_msg_url, json={
        "chat_id": CHANNEL_ID,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": REPLY_MARKUP
    }, timeout=15).json()
    if resp.get('ok'):
        print("✅ Text posted!")
    else:
        print(f"❌ Text error: {resp}")
        exit(1)

# ---------- ইনডেক্স সংরক্ষণ ----------
with open(INDEX_FILE, 'w') as f:
    json.dump(next_index, f)
print(f"💾 Saved index: {next_index}")
