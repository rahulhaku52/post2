import os, json, requests, time, random
from io import BytesIO

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ BOT_TOKEN or CHANNEL_ID not set!")
    exit(1)

INDEX_FILE = "last_index.json"
REPLY_MARKUP = {
    "inline_keyboard": [
        [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/AceR51Tr9VE3Njk1"}]
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

# ---------- ইমেজ জেনারেশন (শুধু Pollinations, ভিন্ন ভিন্ন prompt) ----------
def build_image_prompt(text, index):
    """পোস্টের কন্টেন্ট অনুসারে ভিন্ন ইমেজ প্রম্পট তৈরি করবে"""
    # বেসিক স্টাইল
    base = "cinematic, photorealistic, adult vibe, no nudity, tasteful, aesthetic"

    # পোস্টের কীওয়ার্ড ধরে ভিন্ন দৃশ্য নির্ধারণ
    if "শাড়ি" in text or "saree" in text.lower():
        scene = random.choice([
            "A Bangladeshi woman in a saree lifted above her navel, revealing her panty, wet saree clinging to her body",
            "A woman in a thin saree, blouse open, bra visible, saree falling off her shoulder",
            "A woman in a saree, sitting on a bed, saree draped loosely, blouse unbuttoned, cleavage visible"
        ])
    elif "ব্লাউজ" in text or "blouse" in text.lower():
        scene = random.choice([
            "A woman wearing a tight blouse, top buttons open, bra peeking out, saree slightly lifted",
            "A woman in a blouse and petticoat, blouse partially unbuttoned, one bra strap fallen"
        ])
    elif "প্যান্টি" in text or "panty" in text.lower():
        scene = random.choice([
            "A woman in a thin saree, bent forward, panty line clearly visible through the fabric",
            "A woman lifting her saree to show her panty, shy expression, village background"
        ])
    elif "গুদ" in text or "pussy" in text.lower():
        scene = random.choice([
            "A woman in a saree, wet patch visible on her saree near her navel, sensual look",
            "A woman sitting with legs slightly apart, saree damp between her thighs"
        ])
    elif "শর্টস" in text or "shorts" in text.lower():
        scene = random.choice([
            "A woman in shorts and a crop top, village background, bending forward",
            "A woman wearing tiny shorts, sitting on a chair, legs crossed"
        ])
    else:
        scene = random.choice([
            "A beautiful Bangladeshi woman in a traditional saree, sensual pose, village background",
            "A woman in a nighty, lying on a bed, moody lighting, romantic atmosphere",
            "A woman in a towel, wet hair, standing by a window, rain outside"
        ])

    # ব্যাকগ্রাউন্ড ও সময়
    time_of_day = random.choice(["sunset", "night", "golden hour", "rainy evening", "cloudy afternoon"])
    # র‌্যান্ডম বিস্তারিত
    details = random.choice([
        "intricate details, soft focus, film grain",
        "sharp focus, high contrast, dramatic shadows",
        "soft lighting, dreamy atmosphere"
    ])

    # ইউনিক এলিমেন্ট (index + random)
    unique = f"uid:{index}_{random.randint(1000,9999)}"

    prompt = f"{scene}, {base}, {time_of_day}, {details}, {unique}"
    return prompt[:350]  # খুব বেশি লম্বা নয়

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
prompt = build_image_prompt(caption, next_index)
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
