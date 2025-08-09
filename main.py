import os
import random
import discord
from flask import Flask
import threading
import asyncio
import re
import io
import json
import aiohttp

# -----------------------------------------------------------------------------
# Flask (Render用Webサーバー)
# -----------------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def hello():
    """Renderが正常に起動しているか確認するためのルート"""
    return "Discord Bot is active now"

# -----------------------------------------------------------------------------
# Discordボットの設定
# -----------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

SHOT_TYPE = (
    (4, "紅霊夢A", "紅霊夢B", "紅魔理沙A", "紅魔理沙B"),
    (6, "妖霊夢A", "妖霊夢B", "妖魔理沙A", "妖魔理沙B", "妖咲夜A", "妖咲夜B"),
    (12, "永結界", "永幽冥", "永詠唱", "永紅魔", "永霊夢", "永紫", "永妖夢", "永幽々子", "永魔理沙", "永アリス", "永咲夜", "永レミリア"),
    (6, "風霊夢A", "風霊夢B", "風霊夢C", "風魔理沙A", "風魔理沙B", "風魔理沙C"),
    (6, "地霊夢A", "地霊夢B", "地霊夢C", "地魔理沙A", "地魔理沙B", "地魔理沙C"),
    (6, "星霊夢A", "星霊夢B", "星魔理沙A", "星魔理沙B", "星早苗A", "星早苗B"),
    (4, "神霊夢", "神魔理沙", "神早苗", "神妖夢"),
    (6, "輝霊夢A", "輝霊夢B", "輝魔理沙A", "輝魔理沙B", "輝咲夜A", "輝咲夜B"),
    (4, "紺霊夢", "紺魔理沙", "紺早苗", "紺鈴仙"),
    (16, "春春", "春夏", "春秋", "春冬", "夏春", "夏夏", "夏秋", "夏冬", "秋春", "秋夏", "秋秋", "秋冬", "冬春", "冬夏", "冬秋", "冬冬"),
    (9, "霊夢W", "霊夢E", "霊夢O", "魔理沙W", "魔理沙E", "魔理沙O", "妖夢W", "妖夢E", "妖夢O"),
    (4, "虹霊夢", "虹魔理沙", "虹咲夜", "虹早苗"),
)

STICKER = (
    "<:kazusa:1318960518215766117>", "<:plana1:1318960569822351370>", "<:plana:1318960622268059728>",
    "<:nyny:1318960704249663498>", "<:plana2:1318964188537815150>", "<:usio:1318964272038019132>",
    "<:chiaki:1318964308628996106>",
)

GACHA_TRIGGER = "<:img:1332781427498029106>"
GACHA_STAR_1 = ("<:JYUNYA:921397676166234162>", "<:maiahi:855369574819168266>", "<:emoji_33:901741259260039239>")
GACHA_STAR_2 = ("<:beerjunya:859283357841489950>",)
GACHA_STAR_3 = ("<:rainbowjunya2:930782219490983937>",)
GACHA_ITEMS = [GACHA_STAR_1, GACHA_STAR_2, GACHA_STAR_3, STICKER]
GACHA_WEIGHTS_NORMAL = [78.5, 18.5, 2.3, 0.7]
GACHA_WEIGHTS_GUARANTEED = [0, 18.5 + 78.5, 2.3, 0.7]

# -----------------------------------------------------------------------------
# 画像ダウンロード機能
# -----------------------------------------------------------------------------
async def process_media_link(message, url_type):
    mirror_url = None
    api_url = None
    
    if url_type == 'twitter':
        match = re.search(r'https?://(?:www\.)?(?:x|twitter)\.com/(\w+/status/\d+)', message.content)
        if not match: return
        status_part = match.group(1)
        mirror_url = f"https://vxtwitter.com/{status_part}"
        api_url = f"https://api.fxtwitter.com/{status_part}"

    elif url_type == 'pixiv':
        match = re.search(r'https?://(?:www\.)?pixiv\.net/(?:en/)?artworks/(\d+)', message.content)
        if not match: return
        artwork_id = match.group(1)
        mirror_url = f"https://www.phixiv.net/artworks/{artwork_id}"

    await message.channel.send(mirror_url)

    async with message.channel.typing():
        try:
            image_urls = []
            
            # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
            # 最終解決策：本物のブラウザを装うためのヘッダー情報
            # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
            request_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            }
            
            async with aiohttp.ClientSession() as session:
                if url_type == 'twitter':
                    async with session.get(api_url, headers=request_headers) as resp:
                        if resp.status != 200:
                            await message.channel.send("fxtwitter APIへのアクセスに失敗しました。")
                            return
                        data = await resp.json()
                        media_list = data.get('tweet', {}).get('media', {}).get('all', [])
                        for media in media_list:
                            image_urls.append(media['url'])

                elif url_type == 'pixiv':
                    async with session.get(mirror_url, headers=request_headers) as resp:
                        if resp.status != 200:
                            print(f"phixiv.netへのアクセスに失敗しました。 Status: {resp.status}")
                            await message.channel.send("phixiv.netへのアクセスに失敗しました。")
                            return
                        html = await resp.text()
                    
                    json_match = re.search(r'<script id="application/json">([\s\S]+?)</script>', html)
                    if not json_match:
                        await message.channel.send("phixiv.netから画像情報を見つけられませんでした。")
                        return
                    
                    data = json.loads(json_match.group(1))
                    images = data.get('post', {}).get('images', [])
                    for img_info in images:
                        image_urls.append(img_info.get('urls', {}).get('original'))

                if not image_urls:
                    await message.channel.send("画像が見つかりませんでした。")
                    return
                
                # 画像ダウンロード用のリファラーヘッダー
                download_headers = {'Referer': 'https://www.pixiv.net/'}

                for i, img_url in enumerate(image_urls):
                    if not img_url: continue
                    async with session.get(img_url, headers=download_headers) as img_resp:
                        if img_resp.status == 200:
                            image_data = await img_resp.read()
                            if len(image_data) > 8 * 1024 * 1024:
                                await message.channel.send(f"画像 {i+1} は8MBを超えているため、送信できません。")
                                continue
                            
                            filename = os.path.basename(img_url.split('?')[0])
                            picture = discord.File(io.BytesIO(image_data), filename=filename)
                            await message.channel.send(file=picture)
                        else:
                            await message.channel.send(f"画像 {i+1} のダウンロードに失敗しました。 (Status: {img_resp.status})")

        except Exception as e:
            print(f"An error occurred during media processing: {e}")
            await message.channel.send("画像の処理中にエラーが発生しました。")

def perform_gacha_draw(guaranteed=False):
    weights = GACHA_WEIGHTS_GUARANTEED if guaranteed else GACHA_WEIGHTS_NORMAL
    chosen_category = random.choices(GACHA_ITEMS, weights=weights, k=1)[0]
    return random.choice(chosen_category)

async def send_gacha_results(message):
    results = []
    for _ in range(9):
        results.append(perform_gacha_draw())
    results.append(perform_gacha_draw(guaranteed=True))
    line1 = " ".join(results[0:5])
    line2 = " ".join(results[5:10])
    await message.channel.send(f"{line1}\n{line2}")

def get_random_shot():
    game = random.choice(SHOT_TYPE)
    return random.choice(game[1:])

# -----------------------------------------------------------------------------
# Discordイベント
# -----------------------------------------------------------------------------
@client.event
async def on_ready():
    print(f'Bot準備完了～ Logged in as {client.user}')
    game = discord.Game("説明！ で説明だすよ")
    await client.change_presence(status=discord.Status.online, activity=game)

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
        
    if "x.com" in message.content or "twitter.com" in message.content:
        asyncio.create_task(process_media_link(message, 'twitter'))
        return 

    if "pixiv.net" in message.content:
        asyncio.create_task(process_media_link(message, 'pixiv'))
        return

    if GACHA_TRIGGER in message.content:
        await send_gacha_results(message)
        return
        
    if (client.user.mentioned_in(message) or any(keyword in message.content for keyword in ["本日の機体", "今日の機体", "きょうのきたい", "ほんじつのきたい", "イッツルナティックターイム！"])):
        await message.channel.send(get_random_shot())
        return
    if any(keyword in message.content for keyword in ["にゃ～ん", "にゃーん"]):
        await message.channel.send("にゃ～ん")
        return
    if any(keyword in message.content for keyword in ["説明!", "せつめい!"]):
        await message.channel.send("今日の機体、本日の機体 またはメンションで機体出します")
        return
    if any(keyword in message.content for keyword in ["ソースコード", "そーす"]):
        await message.channel.send("https://github.com/Kakeyouyou33554432/dis_test")
        return
    if any(keyword in message.content for keyword in ["スタンプ", "すたんぷ"]):
        await message.channel.send(random.choice(STICKER))
        return
    if any(s in message.content for s in STICKER) or "💤" in message.content:
        await message.channel.send(random.choice(STICKER))
        return

# -----------------------------------------------------------------------------
# 並列起動
# -----------------------------------------------------------------------------
def run_bot():
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if not bot_token:
        print("DISCORD_BOT_TOKENが設定されていません。")
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.create_task(client.start(bot_token))
    
    if not loop.is_running():
        loop.run_forever()


bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
