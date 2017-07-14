# -*- coding: utf-8 -*-
"""
Created on Sat May 20 22:39:26 2017

@author: Renondedju
"""
import discord
import asyncio
import sys
import traceback
import sqlite3
import os
import re
import pyoppai
import constants
import threading
import recommendation
import update_stats
from datetime import datetime
import requests
from osuapi import OsuMode, BeatmapStatus, OsuApi, ReqConnector
from userlink_key import userlink

#Uso !#7507

client = discord.Client()
commandPrefix = constants.Settings.commandPrefix

api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())
LogFile = open(constants.Paths.logsFile, "a")

mainChannel = None
logsChannel = None
botOwner = None
databasePath = constants.Paths.beatmapDatabase

conn = sqlite3.connect(databasePath)
cursor = conn.cursor()

userlink = userlink(conn)

#Colors
Color_Off='\x1b[0m'
Red='\x1b[1;31;40m'
Yellow='\x1b[1;33;40m'

def IRC()
	os.system("python3.5 /root/UsoBot/IRC/irc_socket.py")

IRC = threading.Thread(target=IRC)
IRC.start()

def return_user_rank(discordId):
	if not discordId == constants.Settings.ownerDiscordId:
		cursor.execute("SELECT rank FROM users WHERE discordId = ?", (str(discordId),))
		try:
			rank = cursor.fetchall()[0][0]
		except IndexError:
			rank = 'USER'
		if rank == "":
			rank = "USER"
		return rank
	return 'MASTER'

def create_backup():
	os.system("cp " + constants.Paths.beatmapDatabase + " " + constants.Paths.backupDirrectory + "DatabaseBackup_"+datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+".db")
	files = os.listdir(constants.Paths.backupDirrectory)
	files.sort()
	if (len(files)>10):
		os.system("rm " + constants.Paths.backupDirrectory + files[0])

def get_user(user = "", mode = OsuMode.osu, discordId = 0, me = True):

	if type(mode) == str:
		if mode == "taiko":
			mode = OsuMode.taiko
		elif mode == "ctb":
			mode = OsuMode.ctb
		elif mode == "mania":
			mode = OsuMode.mania
		else:
			mode = OsuMode.osu

	if user == "me" and me:

		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT OsuId FROM users WHERE discordId = ?", (str(discordId),))
		try:
			osuId = cursor.fetchall()[0][0]
			results = api.get_user(osuId, mode=mode)
		except IndexError:
			results = []
	else:

		user = user.replace("https://osu.ppy.sh/u/", "")
		user = user.replace("https://osu.ppy.sh/users/", "")
		try:
			user = int(user)
		except ValueError:
			pass
		results = api.get_user(user, mode=mode)

	return results

async def change_presence(status, game):
	try:
		await asyncio.sleep(1)
		await client.change_presence(status=status, game=game)
	except websockets.exceptions.ConnectionClosed:
		pass

async def user(channel, mode = "osu", user = "", discordId = 0):
	results = get_user(user = user, mode = mode, discordId = discordId)
	if results == []:
		if user != "me":
			await client.send_message(channel, "Oups sorry, didn't find this user\n*Try with your osu id instead or the link to your profile*")
		else:
			await client.send_message(channel, "Oups sorry, i don't know your osu account :/\nTry the command " + commandPrefix + "link_user your_osu_username to link me to your account")
	else :
		stats = []
		for item in results[0]:
			stats.append(item)
		await User_embed(channel, mode=mode, username=str(stats[17][1]), rank_SS=str(stats[6][1]), rank_S=str(stats[5][1]), rank_A=str(stats[4][1]) , pp=str(stats[13][1]), worldRank=str(stats[12][1]), localRank=str(stats[11][1]), country=stats[7][1], playcount=str(stats[10][1]), level=str(stats[9][1]), osuId = str(stats[16][1]), totalScore = str(stats[15][1]), ranckedScore = str(stats[14][1]), accuracy = str(stats[0][1])[0:4]+"%", hit_300 = str(stats[2][1]), hit_100 = str(stats[1][1]), hit_50 = str(stats[3][1]))

async def send_big_message(channel, message):
	message = message.split("\n")
	finalMessage = ""
	for line in message:
		if len(line) + len(finalMessage) < 2000:
			finalMessage += line + '\n'
		else:
			await client.send_message(channel, finalMessage)
			finalMessage = line + '\n'
	if finalMessage != "":
		await client.send_message(channel, finalMessage)

async def User_embed(channel, old_message = None, title_addition = "",footer_addition = "", mode = "osu" ,username = "Test", pp="1000", rank_SS = "54258", rank_S = "5421", rank_A = "5412", worldRank = "1", localRank = "1", country = "fr", playcount = "10000", level = "100", osuId = "7418575", totalScore = "15105810824020", ranckedScore="8648428841842", accuracy="99.03%", hit_300="532454", hit_100="5324", hit_50="504"):

	if mode not in ['osu', 'taiko', 'mania', 'ctb']:
		mode = 'osu'

	embed = discord.Embed(title = title_addition + " - " + username + " - stats")
	embed.set_thumbnail(url="https://a.ppy.sh/" + osuId)
	if level == "None":
		embed.add_field(name = "Oops !", value="This user haven't played yet in this mode :/")
	else:
		embed.add_field(name="General", value="__Performance:__ **" + pp + "pp\n:map:#" + worldRank + " :flag_"+ country.lower() +":#"+ localRank + "**\n__Playcount:__ **" + playcount + "**\n__Level:__ **" + level + "**", inline=True)
		embed.add_field(name="ᅠ", value="[Profile](https://osu.ppy.sh/users/" + osuId + ") / [Osu!Track](https://ameobea.me/osutrack/user/" + username.replace(" ", "%20") + ") / [PP+](https://syrin.me/pp+/u/"+username.replace(" ", "%20")+") / [Osu!Chan](https://syrin.me/osuchan/u/" + username.replace(" ", "%20") + ")\n__Total score:__ **"+totalScore+"**\n__Ranked score:__ **" + ranckedScore + "**\n__Accuracy:__ **" + accuracy + "**", inline=True)
		embed.add_field(name="Hits (300/100/50)", value="**" + hit_300 + "//" + hit_100 + "//" + hit_50 + "**", inline=True)
		embed.add_field(name="Ranks (SS/S/A)", value="**" + rank_SS + "//" + rank_S + "//" + rank_A + "**", inline=True)
	embed.set_footer(icon_url="https://raw.githubusercontent.com/Lemmmy/osusig/master/img/" + mode +".png", text="Results for " + mode + " mode" + footer_addition)

	if old_message == None:
		message = await client.send_message(channel, embed=embed)
		return message
	else:
		await client.edit_message(old_message, embed=embed)

async def Beatmaps_Embed(channel, beatmaps, approved, title, mode = 'osu'):
	#beatmaps = (title, vesion, mods, pp_100, pp_99, pp_98, ar, cs, od, lenght, drain, stars, combo, beatmapId, beatmapSetId)
	#				0	  1	     2      3      4      5     6   7   8       9     10    11       12       13        14

	description = ""

	if approved == True:
		ranked = 'Ranked'
	else:
		ranked = 'Unranked'

	if mode not in ['osu', 'taiko', 'mania', 'ctb']:
		mode = 'osu'
	if mode == "osu":
		modelink = "osu"
	elif mode == "taiko":
		modelink = "taiko"
	elif mode == "ctb":
		modelink = "fruits"
	else :
		modelink = "mania"

	for beatmap in beatmaps:
		mods = ""
		mods = beatmap[2]
		if mods != "":
			mods = mods.replace("EZ", "<:mod_easy:327800791631134731>")
			mods = mods.replace("SD", "<:mod_suddendeath:327800921113231361>")
			mods = mods.replace("SO", "<:mod_spunout:327800910249984001>")
			mods = mods.replace("HR", "<:mod_hardrock:327800817711054858>")
			mods = mods.replace("PF", "<:mod_perfect:327800879019458571>")
			mods = mods.replace("DT", "<:mod_doubletime:327800759741579265>")
			mods = mods.replace("NC", "<:mod_nightcore:327800859989901312>")
			mods = mods.replace("HD", "<:mod_hidden:328172007931904002>")
			mods = mods.replace("FL", "<:mod_flashlight:327800804037885962>")
			mods = mods.replace("RL", "<:mod_relax:327800900318134273>")
			mods = mods.replace("AP", "<:mod_auto:327800780444794880>")

		print (beatmap)
		lenght = str(int(beatmap[9])//60) + ":" + str(int(beatmap[9])%60)
		drain = str(int(beatmap[10])//60) + ":" + str(int(beatmap[10])%60)
		description += "\n➥ [" + beatmap[0] + "[" + beatmap[1] + "]](https://osu.ppy.sh/beatmapsets/" + str(beatmap[14]) + "#" + modelink + "/" + str(beatmap[13]) + ") " + mods + "\n__100%:__**" + str(beatmap[3]) + "**pp __98%:__**" + str(beatmap[5]) + "**pp"
		description += "** __OD:__**" + str(beatmap[8]) + " __AR:__**" + str(beatmap[6]) + "** __CS:__**" + str(beatmap[7]) + "** **" + lenght + "(" + drain + ")** **" + str(beatmap[11]) + "★** **" + str(beatmap[12]) + "x**\n"

	description = description[:-1]
	embed = discord.Embed(title = title + " (" + str(len(beatmaps)) + ") ▬ " + ranked, description = description)
	embed.set_footer(icon_url="https://raw.githubusercontent.com/Lemmmy/osusig/master/img/" + mode +".png", text="Results for " + mode + " mode")
	await client.send_message(channel, embed=embed)

async def Beatmap_Embed(channel = None ,creator_name = "?", title = "Something", diff_overall = "8.5", diff_size = "5", diff_approach = "9", diff_drain = "9", mods = "HDDTHR", difficultyName = "Too hard for u", bpm = "300", max_combo = "1000", total_length = "255", drain_lenght = "2:35", difficultyrating="8.52", mode='taiko', beatmapSetId = "602313", beatmapId = "1272259", approved=True, pp_100 = "350", pp_99 = "320", pp_98 = "293"):

	if approved == True:
		ranked = 'Ranked'
	else:
		ranked = 'Unranked'

	if mode not in ['osu', 'taiko', 'mania', 'ctb']:
		mode = 'osu'

	if mode == "osu":
		modelink = "osu"
	elif mode == "taiko":
		modelink = "taiko"
	elif mode == "ctb":
		modelink = "fruits"
	else :
		modelink = "mania"

	if mods != "":
		mods = re.sub("(.{10})", "\\1\n", mods, 0, re.DOTALL)
		mods = mods.replace("EZ", "<:mod_easy:327800791631134731>")
		mods = mods.replace("SD", "<:mod_suddendeath:327800921113231361>")
		mods = mods.replace("SO", "<:mod_spunout:327800910249984001>")
		mods = mods.replace("HR", "<:mod_hardrock:327800817711054858>")
		mods = mods.replace("PF", "<:mod_perfect:327800879019458571>")
		mods = mods.replace("DT", "<:mod_doubletime:327800759741579265>")
		mods = mods.replace("NC", "<:mod_nightcore:327800859989901312>")
		mods = mods.replace("HD", "<:mod_hidden:328172007931904002>")
		mods = mods.replace("FL", "<:mod_flashlight:327800804037885962>")
		mods = mods.replace("RL", "<:mod_relax:327800900318134273>")
		mods = mods.replace("AP", "<:mod_auto:327800780444794880>")
	else:
		mods = "No mods"

	total_length = str(int(total_length)//60) + ":" + str(int(total_length)%60)
	drain_lenght = str(int(drain_lenght)//60) + ":" + str(int(drain_lenght)%60)

	embed = discord.Embed(title = title + " - [" + difficultyName + "] ▬ " + ranked, url = "https://osu.ppy.sh/beatmapsets/" + str(beatmapSetId) + "#" + modelink + "/" + str(beatmapId))
	embed.set_thumbnail(url = "https://b.ppy.sh/thumb/" + str(beatmapSetId) + ".jpg")
	embed.add_field(name = "General", value = "__Bpm:__ **" + str(bpm) + "**\n__Max combo:__ **" + str(max_combo) + "x**\n__Length:__ **" + total_length + " (" + drain_lenght + ")**\n__Stars:__ **" + str(round(difficultyrating, 2)) + "★**\nCS:**" + str(diff_size) + "**  OD:**" + str(diff_overall) + "**  AR:**" + str(diff_approach) + "**  HP:**" + str(diff_drain) + "**")
	embed.add_field(name = "ᅠ", value =  "[Download](https://osu.ppy.sh/d/" + str(beatmapSetId) + ") / [No Video](https://osu.ppy.sh/d/" + str(beatmapSetId) + "n) / [Osu!Direct](osu://b/" + str(beatmapId) + ")\n__PP 100%:__ **" + str(round(pp_100)) + "**\n__PP 99%:__ **" + str(round(pp_99)) + "**\n__PP 98%:__ **" + str(round(pp_98)) + "**")
	embed.add_field(name = "Mods", value = mods)
	embed.set_footer(icon_url="https://raw.githubusercontent.com/Lemmmy/osusig/master/img/" + mode +".png", text="Results for " + mode + " mode  -  beatmap by " + creator_name)
	await client.send_message(channel, embed=embed)

async def Log(message, logLevel=0, content="", rank="USER", thumbnailUrl = ""):

	if logLevel == 1:
		LogPrefix = "**WARNING : **"
		LogColor=discord.Colour.gold()
		print (Yellow + LogPrefix + message.author.name + " : " + message.content + Color_Off)
		if content != "":
			print (Yellow + content + Color_Off)
	elif logLevel == 2:
		LogPrefix = "__**ERROR : **__"
		LogColor=discord.Colour.red()
		if content != "":
			print (Red + content + Color_Off)
	else:
		LogPrefix = ""
		LogColor=discord.Colour.default()
		print (LogPrefix + message.author.name + " : " + message.content)
		if content != "":
			print (content)

	date = datetime.now().strftime('%Y/%m/%d at %H:%M:%S')

	if content == "":
		fileOutput = str(logLevel) + str(date) + " -" + str(message.author.name) + " : " + str(message.content)
		LogFile.write(fileOutput + "\n")
		if message.channel.is_private :
			logEmbed = discord.Embed(description = LogPrefix + str(message.channel) + " : " + message.content, colour=LogColor)
		else:
			logEmbed = discord.Embed(description = LogPrefix + str(message.server) + "/" + str(message.channel) + " : " + message.content, colour=LogColor)

		logEmbed.set_footer(text=date)
		if message.author.avatar == None:
			logEmbed.set_author(name = str(message.author.name) + " - " + str(rank))
		else:
			logEmbed.set_author(name = str(message.author.name) + " - " + str(rank), icon_url ="https://cdn.discordapp.com/avatars/"+str(message.author.id)+"/"+message.author.avatar+".png")

		if logLevel == 2:
			await client.send_message(botOwner, embed=logEmbed)

		await client.send_message(logsChannel, embed=logEmbed)
	else:

		fileOutput = str(logLevel) + str(date) + " -" + str(message.author.name) + " : " + str(message.content)
		LogFile.write(fileOutput + "\n")

		logEmbed = discord.Embed(description=content, colour=LogColor)
		logEmbed.set_footer(text=date)
		logEmbed.set_author(name = str(message.author.name), icon_url ="https://cdn.discordapp.com/avatars/"+str(message.author.id)+"/"+message.author.avatar+".png")
		if thumbnailUrl != "":
			logEmbed.set_thumbnail(url=thumbnailUrl)

		if logLevel == 2:
			await client.send_message(botOwner, embed=logEmbed)

		await client.send_message(logsChannel, embed=logEmbed)

@client.event
async def on_ready():
	global mainChannel, logsChannel, visible, databasePath, botOwner
	mainChannel = client.get_server(constants.Settings.mainServerID).get_channel(constants.Settings.mainChannelId)
	logsChannel = client.get_server(constants.Settings.mainServerID).get_channel(constants.Settings.logsChannelId)
	print('Logged in !')

	botOwner = await client.get_user_info(str(constants.Settings.ownerDiscordId))

	await asyncio.sleep(1)
	hello = False
	if datetime.now().strftime('%H') == "02" or (set(sys.argv) & set(["refresh"])):
		await change_presence(status=discord.Status('dnd'), game=discord.Game(name='Booting ...'))
		message = await client.send_message(mainChannel, "<:empty:317951266355544065> Updating stats ...")
		try:
			print('Refreshing users stats ...')
			update_stats.update_all_stats(conn, cursor, api)
			print(" - Done")
			print('Creating new backup ...', end="")
			create_backup()
			print(" Done !")
			await client.edit_message(message, "<:check:317951246084341761> Updating stats ... Done !")
		except:
			await client.edit_message(message, "<:xmark:317951256889131008> Updating stats ... Fail !")
		if not set(sys.argv) & set(["dev"]):
			await client.send_message(mainChannel, "<:online:317951041838514179> Uso!<:Bot:317951180737347587> is now online !")
			await change_presence(status=discord.Status('online'), game=discord.Game(name='Osu !'))
			hello = True
	print ('Ready !')
	if (set(sys.argv) & set(["online"])) and hello == False:
		await client.send_message(mainChannel, "<:online:317951041838514179> Uso!<:Bot:317951180737347587> is now online !")
		await change_presence(status=discord.Status('online'), game=discord.Game(name='o!help'))
	if set(sys.argv) & set(["dev"]):
		await change_presence(status=discord.Status('idle'), game=discord.Game(name='Dev mode'))
 
@client.event
async def on_message(message):
	global api, visible, LogFile, conn, cursor

	rank = 'USER'
	if message.content.startswith(commandPrefix):
		rank = return_user_rank(message.author.id)
		await Log(message, 0, rank=rank)

	channel = message.channel
	if message.content.startswith(commandPrefix) and message.channel.is_private == False and message.content.startswith(commandPrefix + 'mute') == False:
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT state FROM server WHERE serverID = ?", (int(message.server.id),))
		if cursor.fetchall()[0][0] == 'on':
			channel = message.author
		else:
			cursor.execute("SELECT dedicated_channel FROM server WHERE serverID = ?", (int(message.server.id),))
			main_channel = str(cursor.fetchall()[0][0])
			if int(main_channel) == 0:
				channel = message.channel
			else:
				channel = client.get_server(str(message.server.id)).get_channel(str(main_channel))
				if message.channel.id != main_channel and not commandPrefix + 'dedicated_channel' in message.content:
					await client.send_message(channel, message.author.mention + " i'm here ! I'm only allowed to speak in this channel ^^ There is your command result :")

	if message.content.startswith(commandPrefix + 'test') and (rank in ['ADMIN', 'MASTER']):
		embed = discord.Embed(title = "Hi there !", description="[Osu!Direct](osu://b/1262010), [Osu!Direct](osu://s/554297)")	
		await client.send_message(channel, embed = embed)

	if message.content.startswith(commandPrefix + 'backup') and (rank in ['MASTER']):
		create_backup()
		await client.send_message(channel, "Backup done")

	if message.content.startswith(commandPrefix + 'reboot') and (rank in ['ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + "reboot ", "")
		embed = discord.Embed(title = "Reboot", description = "Rebooting using the parameters : " + parameters, colour = discord.Colour.gold())
		await client.send_message(message.channel, embed = embed)
		await Log(message, logLevel=1, content = "Rebooting using the parameters : " + parameters)
		await asyncio.sleep(2)
		os.system("sh " + constants.Paths.workingDirrectory + "reboot_uso.sh " + parameters)

	if message.content.startswith(commandPrefix + 'status') and (rank in ['ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + 'status ', "")
		playmessage = parameters.split(" | ")[0]
		status = parameters.split(" | ")[1]
		await asyncio.sleep(1)
		await client.change_presence(game=discord.Game(name=playmessage), status=discord.Status(status))
		await client.send_message(channel, "Play message set to:``" + playmessage + "``, status set to:``" + status + "``")

	if message.content.startswith(commandPrefix + 'r') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.split("/")
		count = 1
		mods = None
		ranked = True
		Continue = True
		acc = None
		pp = None

		for parameter in parameters:
			if parameter == "":
				await client.send_message(channel, "You need to specify a parameter behind a '/' !\n*/c -> count, /pp -> pp, /r -> ranked, /m -> mods, /a -> accuracy*")
				Continue = False
			elif parameter[0] == "c":
				try:
					count = max(min(int(parameter.replace("count", "").replace("c", "").replace(" ", "")), 5), 1)
				except ValueError:
					Continue = False
					await client.send_message(channel, "The parameter /c *(count)* require a number (between 1 and 5)")

			elif parameter[0] == "p":
				try:
					pp = max(min(int(parameter.replace("p", "").replace("pp", "").replace(" ", "")), 1000), 0)
					mods = ""
					acc = 100
				except ValueError:
					Continue = False
					await client.send_message(channel, "The parameter /pp require a number (between 0 and 1000)")

			elif parameter[0] == "r":
				ranked = parameter.replace("ranked", "").replace("r", "").replace(" ", "").lower() == "true"

			elif parameter[0] == "m":
				temp_mods = parameter.replace("mods", "").replace("mod", "").replace("m", "").replace(" ", "").upper()
				mods = ""
				if "nomod" in temp_mods.lower():
					mods = ""
				if "DT" in temp_mods:
					mods += "DT"
				if "HR" in temp_mods:
					mods += "HR"
				if "HD" in temp_mods:
					mods += "HD"
				if mods != "":
					mods = "_" + mods

			elif parameter[0] == "a":
				try:
					acc = max(min(round(float(parameter.replace("accuracy", "").replace("acc", "").replace("a", "").replace(" ", ""))), 100), 97)
				except ValueError:
					Continue = False
					await client.send_message(channel, "The parameter /a *(accuracy)* require a number (between 97 and 100)")

		if Continue:
			cursor.execute("SELECT * FROM users WHERE DiscordId = ?", [str(message.author.id)])
			result = cursor.fetchall()
			if result != []:
				Recommendations = recommendation.recommendation(str(message.author.id), conn, count = count, mods = mods, ranked = ranked, acc = acc, pp = pp)
				if count > 1:
					beatmaps = []
					for rec in Recommendations:
						#beatmaps = (title, vesion, mods, pp_100, pp_99, pp_98, ar, cs, od, lenght, drain, stars, combo, beatmapId, beatmapSetId)
						beatmaps.append((rec[0], rec[6], rec[5], rec[15], rec[16], rec[17], rec[3], rec[2], rec[1], rec[9], rec[10], rec[11], rec[8], rec[13], rec[12]))
					await Beatmaps_Embed(channel, beatmaps, ranked, "Beatmaps recommendations", pp)
				else:
					rec = Recommendations[0]
					await Beatmap_Embed(channel = channel, title = rec[0], diff_overall = rec[1], diff_size = rec[2], diff_approach = rec[3], diff_drain = rec[4], mods = rec[5], difficultyName = rec[6], bpm = rec[7], max_combo = rec[8], total_length = rec[9], drain_lenght = rec[10], difficultyrating = rec[11], mode = "osu", beatmapSetId = rec[12], beatmapId = rec[13], approved = rec[14], pp_100 = rec[15], pp_99 =rec[16], pp_98 = rec[17], creator_name = rec[18])
			else:
				await client.send_message(channel, "Uhh sorry, seems like you haven't linked your osu! account...\nPlease use the command *" + commandPrefix + "link_user 'Your osu username' or 'your osu Id'* to link the bot to your osu account !\nEx. " + commandPrefix + "link_user Renondedju")

	if message.content.startswith(commandPrefix + 'mute') and (((rank in ['USER']) and message.channel.permissions_for(message.author).administrator == True) or (rank in ['ADMIN', 'MASTER'])):
		if not (message.server.id == None):
			try :
				parameter = message.content.split(' ')[1]
			except:
				parameter = ''
			if parameter.lower() in ['on', 'off']:
				parameter = parameter.lower()
				cursor.execute("SELECT * FROM server WHERE serverID = ?", (str(message.server.id),))
				if len(cursor.fetchall()) == 0:
					cursor.execute("INSERT INTO server (serverID, state) VALUES (?, ?)", (message.server.id, parameter))
				else:
					cursor.execute("UPDATE server SET state = ? WHERE serverID = ?", (parameter, str(message.server.id)))
				await client.send_message(message.channel, "Done !")
				conn.commit()
			else:
				await client.send_message(message.channel, "Wrong argument (expected 'on' or 'off')")
		else:
			await client.send_message(message.channel, "You can't execute this command here (servers only)")

	if message.content.startswith(commandPrefix + 'dedicated_channel') and (((rank in ['USER']) and message.channel.permissions_for(message.author).administrator == True) or (rank in ['ADMIN', 'MASTER'])):
		parameters = message.content.split(' ')
		server_id = message.server.id
		channel_id = message.channel.id
		if channel == message.author:
			await client.send_message(channel, "Oops, you can use this command only on servers !")
		else:
			if parameters[1].lower() == 'set':
				conn = sqlite3.connect(databasePath)
				cursor = conn.cursor()
				cursor.execute("UPDATE server SET dedicated_channel = ? WHERE serverID = ?", (int(channel_id), int(server_id)))
				await client.send_message(message.channel, "<:check:317951246084341761> This channel is now my main channel !")
			elif parameters[1].lower() == 'remove':
				cursor.execute("UPDATE server SET dedicated_channel = ? WHERE serverID = ?", (0, int(server_id)))
				await client.send_message(message.channel, "<:check:317951246084341761> I have no more main channel !")
			else:
				await client.send_message(message.channel, "<:xmark:317951256889131008> Wrong usage : ``o!dedicated_channel <set or remove>``")
			conn.commit()

	if message.content.startswith(commandPrefix + 'kill') and (rank in ['MASTER']):
		if str(message.author.id) == constants.Settings.ownerDiscordId:
			await client.send_message(message.channel, "Alright, killing myself ... bye everyone !")
			client.logout()
			client.close()
			LogFile.close()
			conn.close()
			sys.exit(1)
		else:
			await client.send_message(message.channel, "Sorry, Only Renondedju can do this !")

	if message.content.startswith(commandPrefix + 'user') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + 'user ', "").replace(" osu", "").replace(" mania", "").replace(" ctb", "").replace(" taiko", "")
		if 'taiko' in message.content:
			mode = 'taiko'
		elif 'mania' in message.content:
			mode = 'mania'
		elif 'ctb' in message.content:
			mode = 'ctb'
		else:
			mode = 'osu'

		if parameters == "":
			await client.send_message(channel, "Wrong usage ! `o!user <your osu username/id/url> <mode>` for more informations, use `o!help`\n*Tip: you can use 'me' instead of your username if you linked your osu account with the bot*")
		else:
			await user(channel, user = parameters, mode = mode, discordId= message.author.id)

	if message.content.startswith(commandPrefix + 'link_user') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + 'link_user ', '')
		results = get_user(user = parameters, me = False)

		stats = []
		if not (results == []):
			for item in results[0]:
				stats.append(item)
			osuId = stats[16][1]
			osuUsername = stats[17][1]

			cursor.execute("SELECT * FROM users WHERE discordId = ?", (str(message.author.id),))
			if not cursor.fetchall():
				key = userlink.generate_new_key(osuId, message.author.id)
				
				if message.channel.is_private == False:
					embed = discord.Embed(title = "Link account", description = "Please check your private messages to get your key and the instructions to link your account to uso !", colour = 0x3498db)
					await client.send_message(channel, embed = embed)

				embed = discord.Embed(title = "Link account", colour = 0x3498db, description = "Please open <:osu:310362018773204992> and send me ``pass {}`` (my ingame name is UsoBot)\nBe careful, this key will expire in 10 min\nIf you don't find me, add me as a friend here https://osu.ppy.sh/u/10406668".format(key))
				await client.send_message(message.author, embed = embed)

			else:
				await client.send_message(channel, "Sorry, you already linked your account ! If you have a problem, please contact Renondedju\n➥ <https://discord.gg/mEeMPyK>")

		else:
			await client.send_message(channel, "Oups sorry, didn't find this user\n*Try with your osu id instead or the link to your profile*")

	if message.content.startswith(commandPrefix + 'update_pp_stats') and (rank in ['USER', 'ADMIN', 'MASTER']):
		cursor.execute("SELECT OsuId FROM users WHERE DiscordId = ?", (str(message.author.id),))
		osuId = cursor.fetchall()[0][0]

		if not (osuId == None):
			try:
				update_stats.update_stats(int(message.author.id), conn, api)
				update_pp_message = await client.send_message(channel, "<:check:317951246084341761> Updating your pp stats ... - Done !")
			except update_stats.UserNotInDatabase:
				await client.edit_message(update_pp_message, "<:xmark:317951256889131008> Updating your pp stats ... - Oops ! Wrong osu id.")
			except:
				await client.edit_message(update_pp_message, "<:xmark:317951256889131008> Updating your pp stats ... - Oops ! Unexpected error.")
		else:
			await client.send_message(channel, "Wrong osu! id for " + str(message.author) + ". Try to link your account with an osu account by typing the command *" + commandPrefix + "link_user 'Your osu username'*")

	if message.content.startswith(commandPrefix + 'help') and (rank in ['USER', 'ADMIN', 'MASTER']):
		if not channel.is_private:
			await client.send_message(channel, "You received your help in private message !")
		if rank == 'ADMIN':
			helpfile = open(constants.Paths.helpAdminFile, "r")
			helpString = helpfile.read()
			helpfile.close()
			await send_big_message(message.author, helpString)
		elif rank == 'MASTER':
			helpfile = open(constants.Paths.helpMasterFile, "r")
			helpString = helpfile.read()
			helpfile.close()
			await send_big_message(message.author, helpString)
		else:
			helpfile = open(constants.Paths.helpUserFile, "r")
			helpString = helpfile.read()
			helpfile.close()
			await send_big_message(message.author, helpString)

@client.event
async def on_error(event, *args, **kwargs):
	if len(args) != 0:
		message = args[0]
		channel = message.channel
		if message.content.startswith(commandPrefix) and message.channel.is_private == False and message.content.startswith(commandPrefix + 'mute') == False:
			cursor.execute("SELECT state FROM server WHERE serverID = ?", (str(message.server.id),))
			if cursor.fetchall()[0][0] == 'on':
				channel = message.author
			else:
				channel = message.channel

		print (Red + traceback.format_exc() + Color_Off)
		await Log(message, content = "Message:\n" + message.content + "\n\n```" + traceback.format_exc() + "```", logLevel=2)
		await client.send_message(channel, "Oops ! Unexpected error :/\nGo to my personal server to ask for some help if needed !\n<https://discord.gg/mEeMPyK>")
	else:
		print (Red + traceback.format_exc() + Color_Off)
		message = await client.send_message(logsChannel, "Internal Error !")
		await Log(message, content = "Reason :\n" + message.content + "\n\n```" + traceback.format_exc() + "```", logLevel=2)

@client.event
async def on_server_join(server):
	try:
		cursor.execute("INSERT INTO server (serverID, state) VALUES (?, ?)", (server.id, 'off'))
		conn.commit()
	except sqlite3.IntegrityError:
		print ("Already in database")
	embed = discord.Embed(title = "Hi there !", description="**Nice to meet you, I'm Uso!**\nMy command prefix is ``" + commandPrefix + "``\nIf you want to know what am i capable of, try ``" + commandPrefix + "help``\nAdmins : you can mute me if needed by doing ``" + commandPrefix + "mute on``\n\nAdd the bot to your server [Here](https://discordapp.com/oauth2/authorize?client_id=318357311951208448&scope=bot&permissions=8)\nYou can come to my own server to have some help if nedded or even support the devs :D\n➥https://discord.gg/mEeMPyK\n\n:heart::heart::heart:Have fun evryone !:heart::heart::heart:")	
	embed.set_thumbnail(url = "https://cdn.discordapp.com/avatars/"+str(client.user.id)+"/"+str(client.user.avatar)+".png")
	message = await client.send_message(client.get_server(server.id), embed = embed)
	await Log(message, logLevel = 1, thumbnailUrl = server.icon_url, content = "**I've been added to a new server !**\n__Server name :__ **" + str(server.name) + "**\n__Server Id :__ **" + str(server.id) + "**\n__Users :__ **" + str(server.member_count) + "**\n__Owner name :__ **" + str(server.owner.name) + "**")

@client.event
async def on_server_remove(server):
	message = await client.send_message(logsChannel, "ᅠ")
	await Log(message, logLevel = 1, thumbnailUrl = server.icon_url, content = "**I've been removed from a server !**\n__Server name :__ **" + str(server.name) + "**\n__Server Id :__ **" + str(server.id) + "**\n__Users :__ **" + str(server.member_count) + "**\n__Owner name :__ **" + str(server.owner.name) + "**")

client.run(constants.Api.discordToken)
print("bye !")