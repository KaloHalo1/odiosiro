import discord
from discord.ext import commands
import asyncio
import datetime
import pytz
import os



intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

MODMAIL_CATEGORY_ID = 1396623929036247081

active_tickets = {}

local_tz = pytz.timezone("Europe/Rome")

def get_local_time():
    return datetime.datetime.now(local_tz)

@bot.event
async def on_ready():
    print(f'{bot.user.name} è online!')
    global MODMAIL_CATEGORY_ID
    if MODMAIL_CATEGORY_ID is None:
        for guild in bot.guilds:
            category = discord.utils.get(guild.categories, name="ModMail")
            if category is None:
                category = await guild.create_category("ModMail")
                print(f"Categoria ModMail creata con ID: {category.id}")
            MODMAIL_CATEGORY_ID = category.id
            break

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if isinstance(message.channel, discord.DMChannel):
        await handle_dm(message)

async def handle_dm(message):
    author = message.author
    if author.id in active_tickets:
        channel_id = active_tickets[author.id]
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.dark_grey(),
                timestamp=get_local_time()
            )
            embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar.url if author.avatar else None)
            files = []
            for attachment in message.attachments:
                file = await attachment.to_file()
                files.append(file)
            await channel.send(embed=embed, files=files if files else None)
            await message.add_reaction('✅')
        else:
            del active_tickets[author.id]
            await create_ticket(message)
    else:
        await create_ticket(message)

async def create_ticket(message):
    author = message.author
    for guild in bot.guilds:
        category = discord.utils.get(guild.categories, id=MODMAIL_CATEGORY_ID)
        if not category:
            continue
        channel_name = f"modmail-{author.name}-{author.id}"
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            topic=f"Ticket di ModMail per {author.name}#{author.discriminator} ({author.id})"
        )
        await channel.set_permissions(guild.default_role, read_messages=False)
        active_tickets[author.id] = channel.id
        embed = discord.Embed(
            title="Nuovo Ticket ModMail",
            description=f"Ticket aperto da {author.mention}\n\n**ID Utente:** {author.id}\n**Account creato il:** {author.created_at.strftime('%d/%m/%Y')}\n**Entrato nel server il:** {guild.get_member(author.id).joined_at.strftime('%d/%m/%Y') if guild.get_member(author.id) else 'Non nel server'}",
            color=discord.Color.dark_grey(),
            timestamp=get_local_time()
        )
        embed.set_thumbnail(url=author.avatar.url if author.avatar else None)
        await channel.send(embed=embed)
        content_embed = discord.Embed(
            description=message.content,
            color=discord.Color.dark_grey(),
            timestamp=get_local_time()
        )
        content_embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar.url if author.avatar else None)
        files = []
        for attachment in message.attachments:
            file = await attachment.to_file()
            files.append(file)
        await channel.send(embed=content_embed, files=files if files else None)
        try:
            response_embed = discord.Embed(
                title="Ticket Aperto",
                description="Il tuo messaggio è stato inoltrato allo staff. Riceverai una risposta il prima possibile.",
                color=discord.Color.dark_grey()
            )
            await author.send(embed=response_embed)
        except:
            pass
        await message.add_reaction('✅')
        break

@bot.command()
async def risposta(ctx, *, message=None):
    channel = ctx.channel
    if not channel.name.startswith("modmail-"):
        await ctx.send("Questo comando può essere usato solo nei canali di ModMail.")
        return
    user_id = int(channel.name.split("-")[-1])
    user = bot.get_user(user_id)
    if not user:
        await ctx.send("Non è stato possibile trovare l'utente associato a questo ticket.")
        return
    if not message and not ctx.message.attachments:
        await ctx.send("Per favore, fornisci un messaggio o un allegato da inviare.")
        return
    try:
        files = []
        for attachment in ctx.message.attachments:
            file = await attachment.to_file()
            files.append(file)
        staff_embed = discord.Embed(
            description=message if message else "Allegato dallo staff",
            color=discord.Color.dark_grey(),
            timestamp=get_local_time()
        )
        staff_embed.set_author(name="Venditore di Armi")
        await user.send(embed=staff_embed, files=files if files else None)
        await ctx.send("Messaggio inviato.")
    except Exception as e:
        await ctx.send(f"Errore nell'invio del messaggio: {str(e)}")

@bot.command()
async def chiudi(ctx, *, reason=None):
    channel = ctx.channel
    if not channel.name.startswith("modmail-"):
        await ctx.send("Questo comando può essere usato solo nei canali di ModMail.")
        return
    user_id = int(channel.name.split("-")[-1])
    user = bot.get_user(user_id)
    if user_id in active_tickets:
        del active_tickets[user_id]
    if user:
        close_embed = discord.Embed(
            title="Ticket Chiuso",
            description=f"Il tuo ticket è stato chiuso dallo staff." + (f"\n\nMotivo: {reason}" if reason else ""),
            color=discord.Color.dark_grey(),
            timestamp=get_local_time()
        )
        try:
            await user.send(embed=close_embed)
        except:
            pass
    await ctx.send("Il ticket verrà chiuso tra 5 secondi...")
    await asyncio.sleep(5)
    await channel.delete()

if __name__ == "__main__":
    token = os.getenv("ME_TOKEN")
    if token:
        bot.run(token)
    else:

        print("[ERRORE] ME_TOKEN mancante.")

