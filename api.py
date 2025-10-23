# api.py
import os, random, datetime, asyncio
from flask import Flask, request, jsonify, redirect
import discord
from discord.ext import commands
import requests

app = Flask(__name__)

DISCORD_TOKEN   = os.getenv('DISCORD_TOKEN')
CLIENT_ID       = os.getenv('CLIENT_ID')
CLIENT_SECRET   = os.getenv('CLIENT_SECRET')
REDIRECT_URI    = os.getenv('REDIRECT_URI')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='p!', intents=intents)

logs = []

@bot.event
async def on_ready():
    print(f'{bot.user} hazır!')
    logs.append(f'Bot {bot.user} çevrimiçi oldu.')

@bot.event
async def on_command(ctx):
    logs.append(f'{ctx.author} → {ctx.command}')

@app.route('/api/stats')
def stats():
    return jsonify({
        'servers': len(bot.guilds),
        'users'  : sum(g.member_count for g in bot.guilds),
        'commands': len(Log),
        'logs'   : logs[-5:],
        'dates'  : ['Pzt','Sal','Çar','Per','Cum','Cmt','Paz'],
        'usage'  : [random.randint(10000, 30000) for _ in range(7)]  # DÜZELTİLDİ
    })

@app.route('/api/test-command', methods=['POST'])
async def test_cmd():
    data = request.json
    guild = bot.get_guild(int(data['guild_id']))
    if not guild: return jsonify({'error':'Sunucu bulunamadı'}), 404
    channel = guild.system_channel or guild.text_channels[0]
    cmd = data['command']
    if 'ping' in cmd.lower():
        await channel.send('Pong!')
    logs.append(f'Web-test → {cmd} @ {guild.name}')
    return jsonify({'message':'Başarılı'})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code: return redirect('/')
    TOKEN_DATA = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify guilds'
    }
    token = requests.post('https://discord.com/api/oauth2/token', data=TOKEN_DATA).json()
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    user = requests.get('https://discord.com/api/users/@me', headers=headers).json()
    guilds = requests.get('https://discord.com/api/users/@me/guilds', headers=headers).json()
    bot_guilds = [g for g in guilds if bot.get_guild(int(g['id']))]
    return jsonify({'user': user, 'token': token, 'guilds': bot_guilds})

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(DISCORD_TOKEN))
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
