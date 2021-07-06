import discord
import random
import os
import json
from PIL import Image
from discord.ext import commands
import re
from datetime import datetime
from discord.ext import commands, tasks
from itertools import cycle
import aiofiles
import asyncio
import aiohttp
from io import BytesIO
import time
from discord.ext.commands import Bot

client = commands.Bot(command_prefix = ">")
client.remove_command("help")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def ping(ctx):
  await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
  await member.kick(reason=reason)
  await ctx.send(f"{member.mention} is now kicked")

@kick.error
async def kick_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Mention someone that you would like to kick!")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
  await member.ban(reason=reason)
  await ctx.send(f"{member.mention} is now banned")

@ban.error
async def ban_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Mention someone that you would like to ban")

@client.command(aliases=['forgive'])
@commands.cooldown(1,5,commands.BucketType.user)
async def unban(ctx, *, member):
  banned_users = await ctx.guild.bans()
  member_name, member_discriminator = member.split('#')

  for ban_entry in banned_users:
    user = ban_entry.user

  if(user.name, user.discriminator) == (member_name, member_discriminator):
    await ctx.guild.unban(user)
    await ctx.send(f'Unbanned {user.mention}')

@unban.error
async def unban_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Put there whole name like ``shiv#0001``. **Do not put there id it wont work**")

@client.command(description="Mutes the specified user.")
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
  guild = ctx.guild
  mutedRole = discord.utils.get(guild.roles, name="Muted")

  if not mutedRole:
    mutedRole = await guild.create_role(name="Muted")

    for channel in guild.channels:
      await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)

  await member.add_roles(mutedRole, reason=reason)
  await ctx.send(f"{ctx.author.mention} has muted {member.mention} for `{reason}`. Here is his id `{member.id}`")
  await ctx.message.delete()
  await member.send(f"{ctx.author.mention} has muted you in {guild.name} for `{reason}`!")


@mute.error
async def mute_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Mention someone who you would like to mute!")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def unmute(ctx, member : discord.Member, *, reason=None):
    if (not ctx.author.guild_permissions.manage_messages): 
        await ctx.send('This command requires ``Manage Messages`')
        return
    guild = ctx.guild
    muteRole = discord.utils.get(guild.roles, name="Muted")

    if not muteRole:
       await ctx.send("The muted role has not been found.")
       return

    await member.remove_roles(muteRole, reason=reason)
    await ctx.send(f"{ctx.author.mention} Has unmuted {member.mention} for {reason}. Here is his id `{member.id}`")
    await ctx.message.delete()
    await member.send(f"You have been unmuted from **{guild.name}** | Reason: **{reason}**")

@unmute.error
async def unmute_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Mention someone who you would like to unmute!")

@client.command(pass_text=True)
async def clear(ctx, amount=5):
  if not ctx.author.permissions_in(ctx.channel).manage_messages:
    await ctx.send("Uh-Oh! Looks Like You're Missing The Permission ``Manage_Messages``!")
    return
  if not ctx.author.permissions_in(ctx.channel).manage_messages:
    await ctx.send("Uh-Oh! Looks Like You're Missing The Permission ``Manage_Messages``!")
    return
  await ctx.channel.purge(limit=amount)

@client.command(pass_context=True)
@commands.cooldown(1,5,commands.BucketType.user)
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member:discord.Member, *, role:discord.Role = None):
  await ctx.message.delete()
  await member.add_roles(role)
  await ctx.send(f'{member.mention} Was Given {role} role by {ctx.author.mention}')

@addrole.error
async def addrole_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Please @ who you would like to give the role to!")

@client.command(pass_context=True)
@commands.cooldown(1,5,commands.BucketType.user)
@commands.has_permissions(manage_roles=True)
async def takerole(ctx, member:discord.Member, *, role:discord.Role = None):
  await ctx.message.delete()
  await member.remove_roles(role)
  await ctx.send(f'{role} role was taken from {member.mention}')

@takerole.error
async def takerole_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Please @ who you would like to take the role from!")

@client.command(case_insensitive=True)
@commands.cooldown(1,5,commands.BucketType.user)
async def slowmode(ctx, time: int):
    if (not ctx.author.guild_permissions.manage_messages):
        await ctx.send('Cannot run command! Requires: ``Manage Messages``')
        return
    if time == 0:
        await ctx.send('Slowmode is currently set to `0`')
        await ctx.channel.edit(slowmode_delay=0)
    elif time > 21600:
        await ctx.send('You cannot keep the slowmode higher than 6 hours!')
        return
    else:
        await ctx.channel.edit(slowmode_delay=time)
        await ctx.send(f"Slowmode has been set to `{time}` seconds!")

@slowmode.error
async def slowmode_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Please select a valid time it goes from 0 seconds to 21600s.")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def whois(ctx, *, member: discord.Member):
  def format_time(time):
    return time.strftime('%m/%d/%Y, %H:%M:%S')

  embed = discord.Embed(title=f'{member.name} Info:', color=discord.Color.blurple())

  embed.add_field(name='ID', value=member.id, inline=False)

  embed.set_thumbnail(url=member.avatar_url)

  embed.add_field(name="Created At:", value=format_time(member.created_at))

  embed.add_field(name="Joined At", value=format_time(member.joined_at))

  embed.add_field(name='Roles', value=', '.join(
    role.name for role in member.roles[1:]), inline=False)

  await ctx.send(embed=embed)

@whois.error
async def whois_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Please @ who you would like to see information from!")

@client.command()
async def guilds(ctx):
        if ctx.author.id == 624699940299472896:
            for guild in client.guilds:
                await ctx.send(guild.name)

@client.command()
@commands.has_permissions(manage_channels = True)
async def lock(ctx):
  await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
  await ctx.send(f"{ctx.channel.mention} is now locked by {ctx.author.mention}")

@client.command()
@commands.has_permissions(manage_channels = True)
async def unlock(ctx):
  await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
  await ctx.send(f"{ctx.channel.mention} is now unlocked by {ctx.author.mention}")

@client.command(aliases=['av'])
@commands.cooldown(1, 5, commands.cooldowns.BucketType.user)
async def avatar(ctx, member: discord.Member = None):
    if member == None:
        member = ctx.author

    icon_url = member.avatar_url

    avatarEmbed = discord.Embed(title=f"{member.name}\'s Avatar",
                                color=0xFFA500)

    avatarEmbed.set_image(url=f"{icon_url}")

    avatarEmbed.timestamp = ctx.message.created_at

    await ctx.send(embed=avatarEmbed)

async def open_account(user):
  users = await get_bank_data()

  if str(user.id) in users:
    return False
  else:
    users[str(user.id)] = {}
    users[str(user.id)]["wallet"] = 0
    users[str(user.id)]["bank"] = 250

  with open("bank.json", "w") as f:
    json.dump(users, f, indent=4)
    return True

async def get_bank_data():
  with open("bank.json", "r") as f:
    users = json.load(f)

  return users

async def update_bank(user, change=0, mode="wallet"):
  users = await get_bank_data()

  users[str(user.id)][mode] += change

  with open ("bank.json", "w") as f:
    json.dump(users, f, indent=4)

  bal = [users[str(user.id)]["wallet"], users[str(user.id)]["bank"]]
  return bal

@client.command(aliases=['bal'])
@commands.cooldown(1,5,commands.BucketType.user)
async def balance(ctx, member: discord.Member = None):
  if not member:
    member = ctx.author
  await open_account(member)

  users = await get_bank_data()
  user = member

  wallet_amount =users[str(user.id)]["wallet"]
  bank_amount =users[str(user.id)]["bank"]

  balEmbed = discord.Embed(title = f"{member.name}'s Balance", color = ctx.author.color)
  balEmbed.add_field(name = "wallet", value = wallet_amount)
  balEmbed.add_field(name = "Bank", value = bank_amount)
  await ctx.send(embed = balEmbed)

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def beg(ctx):
  await open_account(ctx.author)

  users = await get_bank_data()
  user = ctx.author
  earnings = random.randrange(400)

  await ctx.send(f"Congrats! Someone gave you {earnings} coins!")

  users[str(user.id)]["wallet"] += earnings

  with open("bank.json", "w") as f:
    json.dump(users, f, indent=4)

@client.command(aliases=['with'])
@commands.cooldown(1,5,commands.BucketType.user)
async def withdraw(ctx, amount=None):
  await open_account(ctx.author)

  if amount == None:
    await ctx.send('Please enter the amount you would like to withdraw')
    return

  bal = await update_bank(ctx.author)

  if amount == "all":
    amount = bal[1]
  elif amount == "max":
    amount = bal[1]

  amount = int(amount)

  if amount < 0:
    await ctx.send('Amount must be larger than 0')
    return
  if amount > bal[1]:
    await ctx.send('You do not have enough money')
    return

  await update_bank(ctx.author,amount,"wallet")
  await update_bank(ctx.author,-1*amount,"bank")

  await ctx.send(f"You withdrew {amount} coins")

@client.command(aliases=['dep'])
@commands.cooldown(1,5,commands.BucketType.user)
async def deposit(ctx, amount=None):
  await open_account(ctx.author)

  if amount == None:
    await ctx.send('Please enter the amount you would like to deposit')
    return

  bal = await update_bank(ctx.author)

  if amount == "all":
    amount = bal[1]
  elif amount == "max":
    amount = bal[1]

  amount = int(amount)

  if amount < 0:
    await ctx.send('Amount must be larger than 0')
    return
  if amount > bal[1]:
    await ctx.send('You do not have enough money')
    return

  await update_bank(ctx.author,-1*amount,"wallet")
  await update_bank(ctx.author,amount,"bank")

  await ctx.send(f"You deposited {amount} coins")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def give(ctx, member:discord.Member, amount=None):
  await open_account(ctx.author)
  await open_account(member)

  if amount == None:
    await ctx.send('Please enter the amount you would like to give')
    return

  bal = await update_bank(ctx.author)

  if amount == "all":
    amount = bal[1]
  elif amount == "max":
    amount = bal[1]

  amount = int(amount)

  if amount < 0:
    await ctx.send('Amount must be larger than 0')
    return
  if amount > bal[1]:
    await ctx.send('You do not have enough money')
    return

  await update_bank(ctx.author,-1*amount,"wallet")
  await update_bank(member,amount,"wallet")

  await ctx.send(f"You gave {member.mention} {amount} coins")

@client.command()
@commands.cooldown(1,5,commands.BucketType.user)
async def rob(ctx, member: discord.Member=None):
  if member == None:
    return await ctx.send('Who will you rob!')
  await open_account(ctx.author)
  await open_account(member)

  bal = await update_bank(member)
  robberBal = await update_bank(ctx.author)
  if robberBal[0]<250:
    return await ctx.send('You need at least 250 coins to rob!')
  else:
    if bal[0]<250:
      return await ctx.send('The person your trying to rob from does not has less than 250 coins')

  stolen = random.randrange(-1*(robberBal[0]), bal[0])

  await update_bank(ctx.author,stolen)
  await update_bank(member,-1* stolen)

  if stolen > 0:
    return await ctx.send(f'You stole {stolen} coins!')
  elif stolen < 0:
    stolen = stolen*-1
    return await ctx.send(f'You tried to steal but got caught... You paid {stolen} coins')

@client.command()
async def massunban(ctx):
  banlist = await ctx.guild.bans()
  for users in banlist:
    try:
      await ctx.guild.unban(user=users.user)
    except:
        pass
  await ctx.send("Mass unbanning")

@client.command()
async def addemoji(ctx, url: str, *, name):
	guild = ctx.guild
	if ctx.author.guild_permissions.manage_emojis:
		async with aiohttp.ClientSession() as ses:
			async with ses.get(url) as r:
				
				try:
					img_or_gif = BytesIO(await r.read())
					b_value = img_or_gif.getvalue()
					if r.status in range(200, 299):
						emoji = await guild.create_custom_emoji(image=b_value, name=name)
						await ctx.send(f'Successfully created emoji: <:{name}:{emoji.id}>')
						await ses.close()
					else:
						await ctx.send(f'Error when making request | {r.status} response.')
						await ses.close()
						
				except discord.HTTPException:
					await ctx.send('File size is too big!')

@client.command()
async def deleteemoji(ctx, emoji: discord.Emoji):
	guild = ctx.guild
	if ctx.author.guild_permissions.manage_emojis:
		await ctx.send(f'Successfully deleted (or not): {emoji}')
		await emoji.delete()

@client.command(pass_context=True)
async def afk(ctx, reason=None):
  current_nick = ctx.author.nick
  await ctx.send(f"{ctx.author.mention} is afk - {reason}")
  await ctx.author.edit(nick=f"[AFK] {ctx.author.mention}")

  counter = 0
  while counter <= int(mins):
    counter += 1
    await asyncio.sleep(60)

    if counter == int(mins):
      await ctx.author.edit(nick=current_nick)
      await ctx.send(f"{ctx.author.mention} is no longer AFK")
      break


@client.group(invoke_without_command=True)
@commands.cooldown(1,5,commands.BucketType.user)
async def help(ctx):
  helpEmbed = discord.Embed(title = "Kef Help", description = "Use >help <command> for extended information", color = ctx.author.color)
  helpEmbed.add_field(name = "Moderation", value = "`ping`,`kick`, `ban`, `unban`, `mute`, `unmute`, `purge`, `addrole`, `takerole`, `slowmode`, `lock`, `unlock`")
  helpEmbed.add_field(name = "Economy Commands", value = "`balance`, `beg`, `withdraw`, `deposit`, `give`, `rob`", inline=False)
  helpEmbed.add_field(name = "Fun commands", value = "`Avatar`, `whois`, `invite`", inline=False)
  await ctx.send(embed = helpEmbed)

@help.command()
async def ping(ctx):

  embed = discord.Embed(title = "Ping", description = "Sends pong", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">ping shows pong with the bot's latency")

  await ctx.send(embed = embed)

@help.command()
async def kick(ctx):

  embed = discord.Embed(title = "Kick", description = "Kicks a memeber from the server", color = ctx.author.color)
  
  embed.add_field(name = "**Example**", value = ">kick ``@member`` [reason]")

  await ctx.send(embed = embed)

@help.command()
async def ban(ctx):

  embed = discord.Embed(title = "ban", description = "bans a memeber from the server", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">ban ``@member`` [reason]")

  await ctx.send(embed = embed)

@help.command()
async def unban(ctx):

  embed = discord.Embed(title = "unban", description = "unbans a memeber from the server", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">unban ``shiv#4136``")

  await ctx.send(embed = embed)

@help.command()
async def mute(ctx):

  embed = discord.Embed(title = "mute", description = "mutes a memeber from the server", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">mute ``@member`` [reason]")

  await ctx.send(embed = embed)

@help.command()
async def unmute(ctx):

  embed = discord.Embed(title = "unmute", description = "unmutes a memeber from the server", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">unmute ``@member`` [reason]")

  await ctx.send(embed = embed)

@help.command()
async def purge(ctx):

  embed = discord.Embed(title = "purge", description = "Deletes all the messages in the channel", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">purge")

  await ctx.send(embed = embed)

@help.command()
async def addrole(ctx):

  embed = discord.Embed(title = "addrole", description = "adds a role to the user you mention", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">addrole ``@member`` [role]")

  await ctx.send(embed = embed)

@help.command()
async def takerole(ctx):

  embed = discord.Embed(title = "Takerole", description = "Takes a role from the user your mention", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">takerole ``@member`` [role]")

  await ctx.send(embed = embed)

@help.command()
async def slowmode(ctx):

  embed = discord.Embed(title = "warn", description = "Warns a user if they are doing something bad and you don't want to mute and give him a chance", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">warn ``@member`` [reason]")

  await ctx.send(embed = embed)

@help.command()
async def whois(ctx):

  embed = discord.Embed(title = "whois", description = "Shows the information about a user", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">whois ``@member``")

  await ctx.send(embed = embed)

@help.command()
async def lock(ctx):

  embed = discord.Embed(title = "lock", description = "Locks the channel", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">lock")

  await ctx.send(embed = embed)

@help.command()
async def unlock(ctx):

  embed = discord.Embed(title = "unlock", description = "unlocks the channel", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">unlock")

  await ctx.send(embed = embed)

@help.command()
async def Join(ctx):

  embed = discord.Embed(title = "Join", description = "Joins the voice channel you are in", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">Join")

  await ctx.send(embed = embed)

@help.command()
async def Leave(ctx):

  embed = discord.Embed(title = "Leave", description = "Leaves the voice channel you are in", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">leave")

  await ctx.send(embed = embed)

@help.command()
async def Play(ctx):

  embed = discord.Embed(title = "Play", description = "Plays the song of your choice. The alias is p", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">play (song) | >p (song)")

  await ctx.send(embed = embed)

@help.command()
async def Queue(ctx):

  embed = discord.Embed(title = "Queue", description = "Plays after the song you are listening to. You dont have to use this command you can also just do `>p (song)` then that song would be added to the queue", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">queue (song)")

  await ctx.send(embed = embed)


@help.command()
async def Pause(ctx):

  embed = discord.Embed(title = "Pause", description = "Pause the song that you are lisntening to", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">pause")

  await ctx.send(embed = embed)

@help.command()
async def Resume(ctx):

  embed = discord.Embed(title = "Resume", description = "Plays the song you paused", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">resume")

  await ctx.send(embed = embed)

@help.command()
async def loop(ctx):

  embed = discord.Embed(title = "loop", description = "Loops the song you are playing", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">loop")

  await ctx.send(embed = embed)

@help.command()
async def Avatar(ctx):

  embed = discord.Embed(title = "Avatar", description = "Shows your avatar or someone else", color = ctx.author.color)

  embed.add_field(name = "**Example**", value = ">avatar")

  await ctx.send(embed = embed)

@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandOnCooldown):
    msg = 'Woah calm down there, please try again in {:.2f}s'.format(error.retry_after)
    await ctx.send(msg)

@client.event
async def on_ready():
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(client.users)} members | >help"))
  print(f' the person that runs {shiv} and he is cute')

@client.command()
async def shiv(ctx):
  embed = discord.Embed(description="shiv...")
  await ctx.send(embed=embed)

@client.command()
async def invite(ctx):
  embed = discord.Embed(description="Invite link: [Bot Link](https://discord.com/api/oauth2/authorize?client_id=856546411159617556&permissions=8&scope=bot)")
  embed.add_field(name="Support Server", value="Invite link: [Server](https://discord.gg/mFUvdUZcHh)")
  await ctx.send(embed=embed)

client.run("ODU2NTQ2NDExMTU5NjE3NTU2.YNCnAg.j4SoVBiVH5RjypsfVxKfnejW32Y")
