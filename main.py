import discord
from discord.ext import commands
from discord.commands import Option
from myinstantsapi import get_sound_url
import json
import aiohttp
import io
import requests
import os
import random


hangmanwords = ["hangman", "python", "discord", "bot", "game", "programming", "computer"]

try:
    try:
      from config import *
    except:
        token=os.getenv("BOT_TOKEN")
        prefix=os.getenv("BOT_PREFIX")
except Exception as e:
    print(e)

sounds=""

async def download_audio_file(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.read()
            content=io.BytesIO(content)
    return content




class SoundView(discord.ui.View):
    def __init__(self, sounds):
        super().__init__()

        chunk_size = 25  # Maximum number of options per select menu
        chunks = [sounds[i:i + chunk_size] for i in range(0, len(sounds), chunk_size)]
        for i, chunk in enumerate(chunks):
          options = [
              discord.SelectOption(label=sound["name"], value=sound["name"], description=f"Choose {sound['name']}!")
              for sound in chunk
          ]

          select_menu = discord.ui.Select(
              placeholder=f"Choose a sound ({i + 1}/{len(chunks)})",
              min_values=1,
              max_values=1,
              options=options,
              custom_id=f"sound_select_{i}",
          )
          select_menu.callback = self.select_callback
          self.add_item(select_menu)
    async def select_callback(self, interaction):
      await interaction.response.defer()
      selected_sound= interaction.data["values"][0]
      for sound in sounds:
        if sound['name'].lower() == selected_sound.lower():
            #msg = await interaction.original_response()
            #await msg.edit("hi")
            sound_url = sound['url'].split(',')[0].replace("'", "")
            print(sound_url)
            audio_content = await download_audio_file(sound_url)
            file = discord.File(audio_content, filename="sound.mp3")
            await interaction.edit_original_response(content=f"The URL for '{selected_sound}' is: {sound_url}", view=None,file=file)
            return
        else:
          pass
      #await interaction.response.send_message(f"Awesome! I like {selected_sound} too!")



class MyModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Short Input"))
        self.add_item(discord.ui.InputText(label="Long Input", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")
        embed.add_field(name="Short Input", value=self.children[0].value)
        embed.add_field(name="Long Input", value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])






intents = discord.Intents.all()
# Create an instance of the bot with a command prefix
bot = commands.Bot(command_prefix=prefix, intents=intents)


# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_message(message):
    print(f"Message received: {message.content} from {message.author} in channel {message.channel}")
    await bot.process_commands(message)



# Command: Ping
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong! Latency: {:.2f}ms'.format(bot.latency * 1000))


@bot.slash_command(name='ping', description='Ping the bot to check latency.')
async def ping(ctx: discord.ApplicationContext):
    await ctx.defer()
    await ctx.respond(f'Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.slash_command(name='mute', description='Mute a User')
async def ping(ctx: discord.ApplicationContext, user: Option(discord.User, "The Member you want to mute", required=True)):
    await ctx.defer(ephemeral=True)
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')

    if not muted_role:
        # If the role doesn't exist, you may want to create it
        muted_role = await ctx.guild.create_role(name='Muted')

    overwrite = discord.PermissionOverwrite(send_messages=False)
    for channel in ctx.guild.text_channels:
        await channel.set_permissions(muted_role, overwrite=overwrite)

    # Add the Muted role to the user
    await user.add_roles(muted_role)



    await ctx.respond(f'Muted {user.mention}', ephemeral= True)

@bot.slash_command(name='unmute', description='Mute a User')
async def ping(ctx: discord.ApplicationContext, user: Option(discord.User, "The Member you want to unmute", required=True)):
    await ctx.defer(ephemeral=True)
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    # Add the Muted role to the user
    await user.remove_roles(muted_role)



    await ctx.respond(f'Muted {user.mention}', ephemeral= True)



@bot.slash_command(name='modal_test', description="example Modal popup")
async def modal_slash(ctx: discord.ApplicationContext):
    """Shows an example of a modal dialog being invoked from a slash command."""
    modal = MyModal(title="Modal via Slash Command")
    await ctx.send_modal(modal)


@bot.slash_command(name='sound', description="Send a sound from myinstants.com")
async def sound(ctx: discord.ApplicationContext, name: Option(str, "The Name of the sound", required=True)):
    await ctx.defer(ephemeral=True)
    global sounds
    sounds=get_sound_url(name,1000)
    sounds=json.loads(sounds)
    view = SoundView(sounds)
    await ctx.respond('Choose the sound you were looking for', view=view, ephemeral=True)

@bot.slash_command(name='clear', description="Clear the entire chat")
async def clear_chat(ctx: discord.ApplicationContext):
    await ctx.defer()
    # Check if the bot has the necessary permissions
    if ctx.guild and ctx.channel.permissions_for(ctx.guild.me).manage_messages:
        try:
            await ctx.channel.purge(limit=None)  # This will delete all messages in the channel
            await ctx.respond("Chat cleared successfully.")
        except discord.Forbidden:
            await ctx.respond("I don't have permission to clear the chat.")
    else:
        await ctx.respond("I don't have the 'Manage Messages' permission to clear the chat.")



@bot.slash_command(name='kick', description='Kick a user from the server!')
async def kick(ctx: discord.ApplicationContext, member: Option(discord.User, "The Member you want to kick", required=True), *, reason:Option(str, "The reason you want to kick him", required=False)):
    await ctx.defer()
    if ctx.author.guild_permissions.kick_members:
        await member.kick(reason=reason)
        await ctx.respond(f'{member.mention} has been kicked from the server. Reason: {reason}')
    else:
        await ctx.respond('You do not have the necessary permissions to use this command.')

@bot.slash_command(name='ban', description='Ban a user from the server')
async def ban(ctx: discord.ApplicationContext, user: Option(discord.User, "The Member you want to ban", required=True) , reason=None):
    await ctx.defer()
    if ctx.author.guild_permissions.ban_members:
        await ctx.guild.ban(user, reason=reason)
        await ctx.respond(f'{user.mention} has been banned from the server. Reason: {reason}')
    else:
        await ctx.respond('You do not have the necessary permissions to use this command.')


@bot.slash_command(name='unban', description='Unban a user from the server')
async def unban(ctx: discord.ApplicationContext, *, member:Option(discord.User, "The Member you want to unban", required=True)):
    await ctx.defer()
    if ctx.author.guild_permissions.ban_members:
        banned_users = await ctx.guild.bans()

        for banned_user in banned_users:
            user = banned_user.user

            if (user.name) == (member):
                await ctx.guild.unban(user)
                await ctx.respond(f'{user.mention} has been unbanned from the server.')
                return

        await ctx.respond(f'{member} not found in the ban list.')
    else:
        await ctx.respond('You do not have the necessary permissions to use this command.')


@bot.slash_command(name='joke', description='Tells a random joke')
async def joke(ctx: discord.ApplicationContext):
    await ctx.defer()
    joke_api_url = 'https://official-joke-api.appspot.com/random_joke'
    try:
        response = requests.get(joke_api_url)
        joke_data = response.json()
        setup = joke_data['setup']
        punchline = joke_data['punchline']

        await ctx.respond(f'**Setup:** {setup}\nCan you guess the punchline? Type your guess within the next 30 seconds.')

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            user_guess = await bot.wait_for('message', timeout=30, check=check)
        except TimeoutError:
            await ctx.respond('Time is up! The correct punchline was: ' + punchline)
            return

        if user_guess.content.lower() == punchline.lower():
            await ctx.respond('Congratulations! You guessed the correct punchline!')
        else:
            await ctx.respond(f"Sorry, that's not the correct punchline. It was: {punchline}")

    except Exception as e:
        print(f"Error fetching joke: {e}")
        await ctx.respond('Sorry, I couldn\'t fetch a joke at the moment.')


async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            img_data = await response.read()
            file = io.BytesIO(img_data)
            return file


@bot.slash_command(name="cat", description="Sends a random cat Image")
async def joke(ctx: discord.ApplicationContext):
    await ctx.defer()
    data = await download_image("https://cataas.com/cat")
    file = discord.File(data, filename="cat.jpeg")
    await ctx.respond(file=file)


@bot.slash_command(name="Hangman", description="Start a game of Hangman")
async def hangman(ctx:discord.ApplicationContext):
    word = random.choice(hangmanwords)
    word_completion = "_" * len(word)
    guessed=False
    guessed_letters=[]
    attempts=6
    await ctx.respond("Will be added soon!")

# Add more commands as needed

# Run the bot with the token
bot.run(token)
