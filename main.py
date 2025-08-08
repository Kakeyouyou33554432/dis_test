import os
import random
import discord
from flask import Flask
import threading
import asyncio

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

# -----------------------------------------------------------------------------
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ここからガチャ機能の追加
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
GACHA_TRIGGER = "<:img:1332781427498029106>"

# ガチャ用のスタンプを定義
GACHA_STAR_1 = ("<:JYUNYA:921397676166234162>", "<:maiahi:1385967824173924354>", "<:emoji_33:901741259260039239>")
GACHA_STAR_2 = ("<:beerjunya:859283357841489950>",)
GACHA_STAR_3 = ("<:rainbowjunya2:930782219490983937>",)

# 各レアリティの抽選アイテムリスト
GACHA_ITEMS = [GACHA_STAR_1, GACHA_STAR_2, GACHA_STAR_3, STICKER]
# 通常の抽選確率
GACHA_WEIGHTS_NORMAL = [78.5, 18.5, 2.3, 0.7]
# 10連目の確定抽選確率 (★1の確率を★2に加算)
GACHA_WEIGHTS_GUARANTEED = [0, 18.5 + 78.5, 2.3, 0.7]

def perform_gacha_draw(guaranteed=False):
    """
    指定された確率でガチャを1回引く
    :param guaranteed: Trueの場合、10連目用の確定確率を使用する
    :return: 当選したスタンプの文字列
    """
    weights = GACHA_WEIGHTS_GUARANTEED if guaranteed else GACHA_WEIGHTS_NORMAL
    # 確率に基づいてレアリティのカテゴリを選択
    chosen_category = random.choices(GACHA_ITEMS, weights=weights, k=1)[0]
    # 選択されたカテゴリの中からランダムに1つのスタンプを選択
    return random.choice(chosen_category)

async def send_gacha_results(message):
    """ガチャを10回実行し、結果を送信する"""
    results = []
    # 1〜9回目は通常の確率で抽選
    for _ in range(9):
        results.append(perform_gacha_draw())
    
    # 10回目は★2以上確定の確率で抽選
    results.append(perform_gacha_draw(guaranteed=True))
    
    # 結果を整形して送信
    await message.channel.send(" ".join(results))

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ガチャ機能の追加ここまで
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

def get_random_shot():
    """インデントエラーを修正"""
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
        
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ガチャのトリガーを追加
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    if GACHA_TRIGGER in message.content:
        await send_gacha_results(message)
        return
        
    if (client.user.mentioned_in(message) or any(keyword in message.content for keyword in ["本日の機体", "今日の機体", "きょうのきたい", "ほんじつのきたい", "イッツルナティックターイム！"])):
        await message.channel.send(get_random_shot())
        return
    if "x.com" in message.content:
        await message.channel.send(message.content.replace("x.com", "vxtwitter.com"))
        return
    if "www.pixiv.net" in message.content:
        await message.channel.send(message.content.replace("www.pixiv.net", "www.phixiv.net"))
        return
    if any(keyword in message.content for keyword in ["にゃ～ん", "にゃーん"]):
        await message.channel.send("にゃ～ん")
        return
    if any(keyword in message.content for keyword in ["説明!", "せつめい!"]):
        await message.channel.send("今日の機体、本日の機体 またはメンションで機体出します")
        return
    if any(keyword in message.content for keyword in ["ソースコード", "そーす"]):
        # ↓↓↓ あなたのGitHubリポジトリのURLに書き換えてください
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

    # asyncioのイベントループを適切に設定
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # client.start()をタスクとして実行
    loop.create_task(client.start(bot_token))
    
    # イベントループを実行し続ける
    if not loop.is_running():
        loop.run_forever()


# Discordボットを別のスレッドで起動する
# Gunicornがこのファイルをインポートして`app`を起動した際に、
# このスレッドも開始される
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
