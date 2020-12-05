#!/usr/bin/env python
# coding: utf-8

import discord
import Voter
import setting

TOKEN = setting.TOKEN
intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print('LOGIN SUCCESS')
    if voter:
        voter.init(client)


@client.event
async def on_message(message):
    if voter:
        if message.content.startswith("/vote"):
            await voter.send_vote_message(message)


@client.event
async def on_reaction_add(reaction, user):
    if voter:
        await voter.reflect_voting(reaction,user)


@client.event
async def on_reaction_remove(reaction, user):
    if voter:
        await voter.cancel_voting(reaction,user)


if __name__ == "__main__":
    voter = Voter.Voter()
    client.run(TOKEN)
