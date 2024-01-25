import discord
from discord.ext import commands
from discord.commands import Option
from config import *
from myinstantsapi import get_sound_url
import json
import aiohttp
import io

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

        self.sounds = sounds
        self.interaction_states = {}  # Dictionary to store the state of each interaction

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
        user_id = interaction.user.id

        # Check if the user is already in an interaction
        if user_id in self.interaction_states:
            await interaction.response.send_message("You are already in an interaction. Please wait.")
            return

        # Set the user's state to processing
        self.interaction_states[user_id] = "processing"

        try:
            await interaction.response.defer()

            selected_sound = interaction.data["values"][0]
            for sound in self.sounds:
                if sound['name'].lower() == selected_sound.lower():
                    sound_url = sound['url'].split(',')[0].replace("'", "")
                    print(sound_url)
                    audio_content = await download_audio_file(sound_url)
                    file = discord.File(audio_content, filename="sound.mp3")

                    # Check if the interaction has been responded to
                    if interaction.response.is_done():
                        await interaction.followup.send(content=f"The URL for '{selected_sound}' is: {sound_url}", file=file)
                    else:
                        await interaction.edit_original_response(content=f"The URL for '{selected_sound}' is: {sound_url}", view=None, file=file)
                    return

            # Check if the interaction has been responded to
            if interaction.response.is_done():
                await interaction.followup.send(f"Selected sound not found: {selected_sound}")
            else:
                await interaction.edit_original_response(f"Selected sound not found: {selected_sound}")
        finally:
            # Clear the user's state
            del self.interaction_states[user_id]





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
    await ctx.respond(f'Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.slash_command(name='mute', description='Mute a User')
async def ping(ctx: discord.ApplicationContext, user: Option(discord.User, "The Member you want to mute", required=True)):
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
async def modal_slash(ctx: discord.ApplicationContext, name: Option(str, "The Name of the sound", required=True)):
    global sounds
    sounds=get_sound_url(name,1000)
    sounds=json.loads(sounds)
    view = SoundView(sounds)
    await ctx.respond(f'Choose the sound you were looking for', view=view, ephemeral=True)





# Add more commands as needed

# Run the bot with the token
bot.run(token)
