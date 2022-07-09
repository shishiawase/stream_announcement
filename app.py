# -*- coding: utf-8 -*-

import httpx
import discord
from random import randint
from discord.ext import tasks
from config import settings


client = httpx.Client()
bot = discord.Client()

### TWITCH ####

def authorize():
    token_params = {
        'client_id': settings['client_id'],
        'client_secret': settings['client_secret'],
        'grant_type': 'client_credentials',
    }
    app_token_request = client.post('https://id.twitch.tv/oauth2/token', params=token_params)
    global twitch_token
    twitch_token = app_token_request.json()

def getStatus():
    headers = {
        'Authorization': f"Bearer {twitch_token['access_token']}",
        'Client-Id': settings['client_id']
    }
    params = {
        'user_login': settings['channel_name']
    }
    global api_status
    api_status = client.get('https://api.twitch.tv/helix/streams', params=params, headers=headers)

### TWITCH ####


### DISCORD ###
check_live = False

@tasks.loop(minutes=5)
async def stream_live(check_live):

    if 'twitch_token' not in globals(): authorize()

    getStatus()
    if api_status.status_code == 200:
        twitch = api_status.json()['data'][0]

        if twitch:
            if not check_live:
                check_live = True
                user_name = twitch['user_name']
                game_name = twitch['game_name']
                title = twitch['title']
                img = twitch['thumbnail_url'].replace("{width}", "1280").replace('{height}', '720')

                embed = discord.Embed(
                    color=randint(0, 0xFFFFFF),
                    title=title,
                    url='https://www.twitch.tv/' + settings['channel_name'],
                    description=f"Началась трансляцию по игре - `{game_name}`.\nНу ты это, заходи если что!\nhttps://www.twitch.tv/{settings['channel_name']}"
                    
                )
                embed.set_thumbnail(url=settings['channel_ico'])
                embed.set_author(name=user_name, icon_url=settings['channel_ico'], url=f"https://www.twitch.tv/{settings['channel_name']}")
                embed.set_image(url=img)

                channel = bot.get_channel(settings['discord_channel'])
                await channel.send('@everyone', embed=embed)
                
        else:
            if check_live: check_live = False
    else: 
        twitch_token = ''
        authorize()
        stream_live(check_live)

@bot.event
async def on_ready():
    print(f"Logged in as: {bot.user.name}")
    stream_live.start(check_live)

bot.run(settings['discord_token'])