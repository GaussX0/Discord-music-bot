import discord
import youtube_dl
import os
import asyncio
from datetime import datetime
from discord.ext import commands, tasks
from re import search
import urllib.request

client=commands.Bot(command_prefix='!')
for file in os.listdir('./'):
    if file.endswith('.webm') or file.endswith('.part'):
        os.remove(file)

songs=[]
full_queue=[] #if you want to loop the songs, you need info about what was in the queue before it finished.
titles=[]
full_titles=[]
channel_info=["name", "channel"] #this stores the info about the channel the bot's connected to
loops=[False, False] #the first value determines if the queue is looped and the second if the current track is looped
@client.event
async def loop_start():
    clear_check.start()
@client.command()
async def join(ctx):
    channel_name = str(ctx.author.voice.channel.name)
    channel=discord.utils.get(ctx.guild.voice_channels, name=channel_name)
    channel_info[0]=channel_name
    channel_info[1]=channel
    voice = ctx.voice_client
    if voice == None:
        await channel.connect()

async def clear_files():
    for file in os.listdir('./'):
        if file.endswith('.webm') or file.endswith('.part'):
            os.remove(file)
@client.command()
async def leave(ctx):
    voice = ctx.voice_client
    if voice != None:
        voice.stop()
        songs.clear()
        titles.clear()
        full_queue.clear()
        full_titles.clear()
        channel_info[0]="name"
        channel_info[1]="channel"
        await ctx.voice_client.disconnect()
        await ctx.send("```yaml\nLeft the voice channel.```")
    else:
        await ctx.send("```yaml\nI'm not even in a voice channel, stupid.```")
    try:
        await clear_files()
    except PermissionError:
        await asyncio.sleep(0.5)
        await clear_files()

async def bot_play(ctx, songs: list, titles):
    while len(songs)>0:
        for song in songs:
            if song.endswith('.webm'):
                voice = ctx.voice_client
                await ctx.send('```yaml\nNow playing - '+titles[0]+'.```')
                voice.play(discord.FFmpegOpusAudio(song))
                while voice.is_playing():
                    await asyncio.sleep(1)
                if len(songs)>0 and not loops[1]:
                    songs.pop(0)
                    titles.pop(0)
                if len(songs)==0 and loops[0]:
                    songs=full_queue.copy()
                    titles=full_titles.copy()
                print(titles)

@client.command(name='play', help='Plays the song you request, usage: !play /url/ or !play /song name/')
async def play(ctx, *args):
    url_="+".join(args)
    voice = ctx.voice_client
    print(url_)
    if voice != None:
        channel_name=channel_info[0]
        channel=channel_info[1]
    else:
        channel_name = str(ctx.author.voice.channel.name)
        channel=discord.utils.get(ctx.guild.voice_channels, name=channel_name)
        channel_info[0]=channel_name
        channel_info[1]=channel
    if voice == None:
        await channel.connect()
    else:
        if ctx.author.voice.channel.name != channel_info[0]:
            await ctx.send("```yaml\nFuck you, I'm playing for "+channel_name+" right now.```")
            return 0
    ydl_args={
        'format': '249/250/251',
    }
    if url_.startswith('https://www.youtube.com') or url_.startswith('www.youtube.com') or url_.startswith('youtube.com'):
        result=url_
    else:
        print(url_)
        site=urllib.request.urlopen("https://www.youtube.com/results?search_query="+url_)
        found=search(r".watch\?v=(\S{11}).", site.read().decode())
        #if type(found==None):
        #    await ctx.send("```yaml\nThere are no videos that match your query OR they're family unfriendly.```")
        #   return 0
        result="https://www.youtube.com/watch?v="+found.group(1)
    sum = str(datetime.now().timestamp())
    youtube_dl.YoutubeDL(ydl_args).download([result])
    for file in os.listdir('./'):
        if file.endswith('.webm') and not file.startswith('song'):
            titles.append(str(file)[:-17])
            full_titles.append(str(file)[:-17])
            if len(songs)>0:
                await ctx.send("```yaml\nQueued "+str(file)[:-17]+".```")
            os.rename(file, 'song'+str(sum)+'.webm')
            songs.append('song'+str(sum)+'.webm')
            full_queue.append('song'+str(sum)+'.webm')
    print(songs)
    voice=ctx.voice_client
    if voice==None:
        await join(ctx)
    if not voice.is_playing():
        await bot_play(ctx, songs, titles)

@client.command()
async def p(ctx, *args):
    await play(ctx, *args)

@client.command()
async def P(ctx, *args):
    await play(ctx, *args)


@client.command()
async def pause(ctx):
    voice=ctx.voice_client
    if voice.is_playing():
        voice.pause()
    await ctx.send('```yaml\nPaused.```')
    
@client.command()
async def resume(ctx):
    voice=ctx.voice_client
    if not voice.is_playing():
        voice.resume()
    await ctx.send('```yaml\nResuming...```')
    
@client.command(name="stop", help="Stops the bot from playing every song that's queued, un-loops, but the songs are still queued and will be looped if !loop is passed.")
async def stop(ctx):
    voice=ctx.voice_client
    voice.stop()
    songs.clear()
    titles.clear()
    loops[0]=False
    loops[1]=False
    await ctx.send('```yaml\nStopped.```')

@client.command(name="empty_queue", help="Empties the queue. Useful for when you don't want some of the songs looping.")
async def empty_queue(ctx):
    voice=ctx.voice_client
    full_queue.clear()
    titles.clear()
    full_titles.clear()
    voice.stop()
    songs.clear()
    await ctx.send('```yaml\nQueue emptied.```')
    try:
        await clear_files()
    except PermissionError:
        await asyncio.sleep(0.5)
        await clear_files()

@client.command(name="skip", help="Skips the current song.")
async def skip(ctx):
    if ctx.author.voice.channel.name != channel_info[0]:
        await ctx.send("```yaml\nYou're not even listening to the music, retard.```")
    voice=ctx.voice_client
    if not voice==None:
        if voice.is_playing():
            voice.stop()
    if(len(songs)>0):
        songs.pop(0)
        await ctx.send('```yaml\nSkipped.```')
        await bot_play(ctx, songs, titles)
    else:
        await ctx.send('```yaml\nNothing to skip.```')

@client.command(name="s", help="Same as skip.")
async def s(ctx):
    await skip(ctx)

@client.command(name="fs", help="Same as skip, derived from f(orce)s(kip)")
async def fs(ctx):
    await skip(ctx)

@client.command()
async def print_list(ctx):
    await ctx.send(songs)

@client.command()
async def queue(ctx):
    iter=1
    message="```yaml\nCurrently playing: "+titles[0]
    for title in titles[1:]:
        message+='\n'+str(iter)+'. '+title
        iter+=1
    message+=('```')
    await ctx.send(message)
@client.command()
async def q(ctx):
    await queue(ctx)

async def true_loop(ctx, loops):
    if not loops[0] and not loops[1]:
        loops[0]=True
        await ctx.send("```yaml\nThe queue is now looped.```")
    elif loops[0] and not loops[1]:
        loops[0]=False
        loops[1]=True
        await ctx.send("```yaml\nThe current track is now looped.```")
    else:
        loops[1]=False
        await ctx.send("```yaml\nLooping disabled.```")

@client.command()
async def loop(ctx):
    await true_loop(ctx, loops)

@client.command()
async def remove(ctx, position:int):
    if position<1 or position>=len(songs):
        await ctx.send("```yaml\nThis is not a valid queue position! If you want to skip the current song, use !skip, otherwise check !queue and pick a valid number.```")
        return 0
    full_queue.pop(full_queue.index(songs[position]))
    songs.pop(position)
    full_titles.pop(full_titles.index(titles[position]))
    await ctx.send('```yaml\nSuccessfully removed '+titles[position]+' from the queue.```')
    titles.pop(position)

@tasks.loop(seconds=300)
async def clear_check(ctx):
    if ctx.voice_client==None:
        await clear_files()
print("GaussBot operational!")
your_token = 'urtoken' #replace the value with your bot's token
client.run(your_token)