import os, json, random, requests, time

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

INDEX_FILE = "posted_index.json"

def generate_image_pollinations(prompt):
    """Pollinations.ai দিয়ে ইমেজ তৈরি (ফ্রি, কোনো API Key লাগবে না)"""
    try:
        # প্রম্পট ইংরেজিতে কনভার্ট করার দরকার নেই, শুধু URL-encode
        encoded = requests.utils.quote(prompt[:200])  # খুব বড় প্রম্পট নয়
        url = f"https://image.pollinations.ai/prompt/{encoded}"
        # কখনো কখনো প্রথমবার ফল দিতে দেরি হয়, তাই ৩ বার ট্রাই
        for attempt in range(3):
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.content
            elif resp.status_code == 503:
                print(f"⏳ Pollinations busy, retry {attempt+1}/3")
                time.sleep(5)
            else:
                print(f"❌ Pollinations error: {resp.status_code}")
                break
        return None
    except Exception as e:
        print(f"❌ Pollinations exception: {e}")
        return None

def send_photo(image_bytes, caption=""):
    """টেলিগ্রামে ফটো পাঠাবে"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': ('image.jpg', image_bytes, 'image/jpeg')}
    data = {
        'chat_id': CHANNEL_ID,
        'caption': caption[:1024],  # টেলিগ্রাম ক্যাপশন লিমিট
        'parse_mode': 'HTML'
    }
    resp = requests.post(url, files=files, data=data, timeout=30)
    return resp.json()

# -------- মূল লজিক --------
# পোস্ট লোড
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)
total = len(posts)
print(f"📊 Total posts: {total}")

# ইনডেক্স লোড
try:
    with open(INDEX_FILE, 'r') as f:
        posted = set(json.load(f))
    print(f"📂 Loaded {len(posted)} posted indices")
except:
    posted = set()
    print("📂 No previous posted indices. Starting fresh.")

# সব পোস্ট শেষ হলে রিসেট
if len(posted) >= total:
    print("🔄 All posts have been posted. Resetting.")
    posted = set()

available = [i for i in range(total) if i not in posted]
if not available:
    print("❌ No available posts (should not happen)")
    exit(1)

next_index = random.choice(available)
post = posts[next_index]
text = post.get('text', '')
print(f"🎲 Random index: {next_index} (0-{total-1})")
print(f"📝 Post: {text[:60]}...")

# ইমেজ প্রম্পট: টেক্সটের প্রথম ১৫০ ক্যারেক্টার + সিনেমাটিক কিওয়ার্ড
prompt_text = text[:150].strip()
# ইংরেজি না হলেও চলবে, Pollinations কিছুটা বাংলা বুঝে? আসলে দরকার ইংরেজি।
# তাই আমরা টেক্সটের সাথে কিছু কিওয়ার্ড যোগ করব
prompt = f"{prompt_text}, romantic, couple, sensual, cinematic, realistic, attractive"

print(f"🖼️ Image prompt: {prompt[:100]}...")

# ইমেজ জেনারেট
image_bytes = generate_image_pollinations(prompt)

photo_sent = False
if image_bytes:
    # ক্যাপশন হিসেবে পুরো টেক্সট (খুব বড় হলে ছোট করে)
    caption = text[:300] + "\n\n🔗 Join Our List: https://t.me/addlist/57pQLQQl0Oo1MDk9"
    res = send_photo(image_bytes, caption)
    if res.get('ok'):
        print("✅ Photo sent!")
        photo_sent = True
    else:
        print(f"❌ Photo send error: {res}")

# ছবি না পাঠাতে পারলে টেক্সট-only
if not photo_sent:
    print("📝 Sending text only...")
    reply_markup = {
        "inline_keyboard": [
            [{"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}]
        ]
    }
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, json={
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

# সফল হলে ইনডেক্স সেভ
posted.add(next_index)
with open(INDEX_FILE, 'w') as f:
    json.dump(list(posted), f)
print(f"💾 Saved posted indices. Total posted: {len(posted)}")
