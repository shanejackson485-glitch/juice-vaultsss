import os, aiohttp, discord
from discord.ext import commands
API=os.getenv('VAULT_API_URL','http://127.0.0.1:8000').rstrip('/')
KEY=os.getenv('VAULT_API_KEY','')
bot=commands.Bot(command_prefix=',',intents=discord.Intents.default())
async def api_get(path,params=None):
    headers={'X-API-Key':KEY} if KEY else {}
    async with aiohttp.ClientSession(headers=headers,timeout=aiohttp.ClientTimeout(total=15)) as s:
        async with s.get(API+path,params=params) as r:r.raise_for_status();return await r.json()
@bot.command(name='wrld')
async def wrld(ctx,*,query:str):
    try:
        payload=await api_get('/api/v1/search',{'q':query,'limit':5});songs=payload.get('data',{}).get('songs',[])
        if not songs:return await ctx.reply('No songs found.')
        song=songs[0];embed=discord.Embed(title=song.get('title','Unknown'),url=song.get('url'),description=f"**Status:** {song.get('status','Unknown').title()}\n**Era:** {song.get('era') or 'Unknown'}\n**Version:** {song.get('versionLabel') or 'Main version'}",color=discord.Color.from_rgb(43,45,49))
        if song.get('cover'):embed.set_thumbnail(url=song['cover'])
        embed.set_footer(text='Juice WRLD Vault API · Catalogue data: juicewrld.io');await ctx.reply(embed=embed)
    except Exception as e:await ctx.reply(f'Vault API error: {e}')
@bot.command(name='wrldstats')
async def wrldstats(ctx):
    try:
        d=(await api_get('/api/v1/stats')).get('data',{});e=discord.Embed(title='🕊️ Juice WRLD Vault Statistics',color=discord.Color.from_rgb(43,45,49))
        for label,key in [('Songs','songs'),('Versions','versions'),('Sessions','studioSessions'),('Eras','eras'),('Projects','projects'),('People','people')]:e.add_field(name=label,value=f'{d.get(key,0):,}',inline=True)
        await ctx.reply(embed=e)
    except Exception as ex:await ctx.reply(f'Vault API error: {ex}')
bot.run(os.environ['DISCORD_TOKEN'])
