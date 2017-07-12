#!/usr/bin/env python3

from twitterAPI.twitter import *
import json
import discord
import threading
import asyncio
import os
from shutil import copyfile

config = json.load(open("config.json"))
client = discord.Client()

if not os.path.exists('config.json'):
    copyfile('config.sample.json', 'config.json')


def twitter_thread():
    auth = OAuth(
        consumer_key=config['twitterTokens']['consumer_key'],
        consumer_secret=config['twitterTokens']['consumer_secret'],
        token=config['twitterTokens']['token'],
        token_secret=config['twitterTokens']['token_secret']
    )
    twitter_userstream = TwitterStream(auth=auth, domain='userstream.twitter.com')

    t = Twitter(auth=auth)

    members_id_list = []
    for member in t.lists.members(owner_screen_name=t.account.settings()['screen_name'],
                                  slug=config['twitterListName'])['users']:
        members_id_list.append(member['id'])

    while not client.is_closed:
        for msg in twitter_userstream.user():
            if client.is_closed:
                return
            if 'event' in msg:
                if msg['event'] == 'favorite' and msg['target']['id'] in members_id_list:
                    images = msg['target_object']['extended_entities']['media']
                    for img in images:
                        asyncio.ensure_future(
                            client.send_message(client.get_channel(config['discordChannelID']), img['media_url']),
                            loop=client.loop
                        )
                if msg['event'] == 'list_member_added' and msg['target_object']['slug'] == config['twitterListName']:
                    members_id_list.append(msg['target']['id'])
                if msg['event'] == 'list_member_removed' and msg['target_object']['slug'] == config['twitterListName']:
                    members_id_list.remove(msg['target']['id'])


thread = threading.Thread(target=twitter_thread)


@client.event
async def on_ready():
    thread.start()
    print('Bot ready')


print('TwitterFav2Discord\n')
client.run(config['discordToken'])
print('Bot is stopping...')
