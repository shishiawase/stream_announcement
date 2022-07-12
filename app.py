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
    global headers
    headers = {
        'Authorization': f"Bearer {twitch_token['access_token']}",
        'Client-Id': settings['client_id']
    }

def getStream():
    params = {
        'user_login': settings['channel_name']
    }
    stream = client.get('https://api.twitch.tv/helix/streams', params=params, headers=headers)

    while stream.status_code != 200:
        authorize()
        stream = client.get('https://api.twitch.tv/helix/streams', params=params, headers=headers)
    return stream.json()['data']

def user_ico():
    params = {
        'login': settings['channel_name']
    }
    res = client.get('https://api.twitch.tv/helix/users', params=params, headers=headers)
    while res.status_code != 200:
        authorize()
        res = client.get('https://api.twitch.tv/helix/users', params=params, headers=headers)
    return res['data'][0]['profile_image_url']

### TWITCH ####


### DISCORD ###
check_live = False

@tasks.loop(minutes=5)
async def stream_live():

    global check_live
    if 'twitch_token' not in globals(): authorize()
    
    twitch = getStream()

    if twitch:
        if not check_live:
            check_live = True
            user_name = twitch[0]['user_name']
            game_name = twitch[0]['game_name']
            title = twitch[0]['title']
            img = twitch[0]['thumbnail_url'].replace("{width}", "1280").replace('{height}', '720')
            icon = user_ico()

            embed = discord.Embed(
                color=randint(0, 0xFFFFFF),
                title=title,
                url='https://www.twitch.tv/' + settings['channel_name'],
                description=f"Началась трансляцию по игре - `{game_name}`.\nНу ты это, заходи если что!\nhttps://www.twitch.tv/{settings['channel_name']}"    
            )
            embed.set_thumbnail(url=icon)
            embed.set_author(name=user_name, icon_url=icon, url=f"https://www.twitch.tv/{settings['channel_name']}")
            embed.set_image(url=img)

            channel = bot.get_channel(settings['discord_channel'])
            await channel.send('@everyone', embed=embed)
                
    else:
        if check_live:
            check_live = False

@bot.event
async def on_ready():
    print(f"Logged in as: {bot.user.name}")
    stream_live.start()

bot.run(settings['discord_token'])
