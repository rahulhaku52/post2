import os, json, requests

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ BOT_TOKEN or CHANNEL_ID not set!")
    exit(1)

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

# 🔥 ইনলাইন বাটন তৈরি (শুধু এই অংশ যোগ)
reply_markup = {
    "inline_keyboard": [
        [
            {"text": "🔗 Join Our List", "url": "https://t.me/addlist/57pQLQQl0Oo1MDk9"}
        ]
    ]
}

# টেলিগ্রামে পাঠান
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
res = requests.post(url, json={
    "chat_id": CHANNEL_ID,
    "text": text,
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
    "reply_markup": reply_markup   # ← এই লাইন যোগ
}, timeout=15).json()

if res.get('ok'):
    print("✅ Posted!")
else:
    print(f"❌ Telegram error: {res}")
    exit(1)

# সেভ (ক্যাশ এই ফাইলটা সংরক্ষণ করবে)
with open(INDEX_FILE, 'w') as f:
    json.dump(next_index, f)
print(f"💾 Saved index: {next_index}")
