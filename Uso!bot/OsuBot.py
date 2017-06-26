# -*- coding: utf-8 -*-
"""
Created on Sat May 20 22:39:26 2017

@author: Renondedju
"""
import discord
import asyncio
import sys
import traceback
import subprocess
import sqlite3
import os
import re
from datetime import datetime
from osuapi import OsuApi, ReqConnector, OsuMode, BeatmapStatus
import requests
import constants

#Uso !#7507

client = discord.Client()
commandPrefix = constants.Settings.commandPrefix

api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())
LogFile = open(constants.Paths.logsFile, "a")

mainChannel = None
logsChannel = None
botOwner = None
databasePath = constants.Paths.beatmapDatabase

#Colors
Color_Off='\x1b[0m'
Red='\x1b[1;31;40m'
Yellow='\x1b[1;33;40m'

def return_user_rank(discordId):
	if not discordId == constants.Settings.ownerDiscordId:
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT rank FROM users WHERE discordId = ?", (str(discordId),))
		try:
			rank = cursor.fetchall()[0][0]
		except IndexError:
			rank = 'USER'
		conn.close()
		if rank == "":
			rank = "USER"
		return rank
	return 'MASTER'

def refresh_all_pp_stats():
	conn = sqlite3.connect(databasePath)
	cursor = conn.cursor()
	cursor.execute("SELECT DiscordId, OsuId FROM users")
	usersToRefresh = cursor.fetchall()
	for user in usersToRefresh:
		update_pp_stats(user[1], user[0])

def update_pp_stats(osuId, discordId):
	try:
		pp_average = get_pp_stats(osuId)
		if pp_average == False:
			return 1
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("UPDATE users SET ppAverage = ? WHERE DiscordId = ?", (str(pp_average), str(discordId),))
		conn.commit()
		print ("Pp stats updated for osuId : " + str(osuId) + " with discordId : " + str(discordId) + " - PP average = " + str(pp_average))
		return 0
	except:
		return 2

def get_pp_stats(osuId):
	global api
	try:
		results = api.get_user_best(osuId, limit = 20)
		pp_average = 0
		for beatmap in results:
			for item in beatmap:
				if item[0] == 'pp':
					pp_average += item[1]
		pp_average = pp_average/20
		return pp_average
	except:
		return False

def link_user(discordId, osuName, osuId, rank):
	result = ""
	print ("Linking : discordId : " + str(discordId) + ", osuName : " + osuName + ", osuId : " + str(osuId) + " to Database.", end = " ")
	conn = sqlite3.connect(databasePath)
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM users WHERE discordId = ?", (str(discordId),))
	if len(cursor.fetchall()) == 0:
		cursor.execute("""
		INSERT INTO users (discordId, osuName, osuId, rank) 
		VALUES (?, ?, ?, ?)
		""", (discordId, osuName, osuId, rank))
		conn.commit()
		print ("Added")
		result = "linked"
	else:
		cursor.execute("UPDATE users SET osuName = ?, osuId = ?, rank = ? WHERE discordId = ?", (osuName, str(osuId), rank, str(discordId)))
		conn.commit()
		print("Updated")
		result = "updated"
	conn.close()
	return result

def add_beatmap_to_queue(url):
	if not(url in new_beatmap_list):
		new_beatmaps_file = open("/home/pi/DiscordBots/OsuBot/beatmapsFiles/newBeatmaps.txt", "a")
		new_beatmaps_file.write('\n' + url)
		new_beatmaps_file.close()
		print ("Added " + url + " to beatmap queue")

def return_simple_beatmap_info(url, oppaiParameters):
	url = url.replace('/b/', '/osu/').split("&", 1)[0]
	if oppaiParameters == "":
		command = "curl " + url + " | /home/pi/DiscordBots/Oppai/oppai/oppai -"
	else:
		command = "curl " + url + " | /home/pi/DiscordBots/Oppai/oppai/oppai - " + oppaiParameters

	return get_infos(subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).stdout.read())

def return_beatmap_infos(url, oppaiParameters):
	#https://osu.ppy.sh/osu/37658
	url = url.replace('/b/', '/osu/').split("&", 1)[0]
	if oppaiParameters == "":
		command = "curl " + url + " | /home/pi/DiscordBots/Oppai/oppai/oppai -"
	else:
		command = "curl " + url + " | /home/pi/DiscordBots/Oppai/oppai/oppai - " + oppaiParameters

	#print (command)
	p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	raw_data = p.stdout.read()
	pp_100, name, combo, stars, diff_params = get_infos(raw_data)
	if pp_100 == -1:
		pp_100 = pp_95 = name = combo = stars = diff_params = -1
		return pp_100, pp_95, name, combo, stars, diff_params
	else:
		p = subprocess.Popen(command + " 95%", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		raw_data = p.stdout.read()
		pp_95, _, _, _, _ = get_infos(raw_data)
		return pp_100, pp_95, name, combo, stars, diff_params

def get_infos(row_datas):
	try:
		split_data = row_datas.split(b'\n')
		pp = split_data[35].replace(b'pp', b'').decode("utf-8")
		name = split_data[14].replace(b' - ', b'').decode("utf-8")
		combo = split_data[16].split(b'/')[0].decode("utf-8")
		stars = split_data[22].replace(b' stars', b'').decode("utf-8")
		diff_params = split_data[15].decode("utf-8")
		return pp, name, combo, stars, diff_params
	except:
		pp = name = combo = stars = diff_params = -1
		return pp, name, combo, stars, diff_params

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
		osuId = cursor.fetchall()[0][0]
		results = api.get_user(osuId, mode=mode)
	else:

		user = user.replace("https://osu.ppy.sh/u/", "")
		user = user.replace("https://osu.ppy.sh/users/", "")
		try:
			user = int(user)
		except ValueError:
			user = str(user) #Just to fill
		results = api.get_user(user, mode=mode)

	return results

async def user(channel, mode = "osu", user = "", discordId = 0):
	results = get_user(user = user, mode = mode, discordId = discordId)
	if results == []:
		await client.send_message(channel, "Oups sorry, didn't find this user\n*Try with your osu id instead or the link to your profile*")
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

async def User_embed(channel, mode = "osu" ,username = "Test", pp="1000", rank_SS = "54258", rank_S = "5421", rank_A = "5412", worldRank = "1", localRank = "1", country = "fr", playcount = "10000", level = "100", osuId = "7418575", totalScore = "15105810824020", ranckedScore="8648428841842", accuracy="99.03%", hit_300="532454", hit_100="5324", hit_50="504"):

	if mode not in ['osu', 'taiko', 'mania', 'ctb']:
		mode = 'osu'

	embed = discord.Embed(title = "- " + username + " - stats")
	embed.set_thumbnail(url="https://a.ppy.sh/" + osuId)
	if level == "None":
		embed.add_field(name = "Oops !", value="This user haven't played yet in this mode :/")
	else:
		embed.add_field(name="General", value="__Performance:__ **" + pp + "pp\n:map:#" + worldRank + " :flag_"+ country.lower() +":#"+ localRank + "**\n__Playcount:__ **" + playcount + "**\n__Level:__ **" + level + "**", inline=True)
		embed.add_field(name="ᅠ", value="[Profile](https://osu.ppy.sh/users/" + osuId + ") / [Osu!Track](https://ameobea.me/osutrack/user/" + username.replace(" ", "%20") + ") / [PP+](https://syrin.me/pp+/u/"+username.replace(" ", "%20")+") / [Osu!Chan](https://syrin.me/osuchan/u/" + username.replace(" ", "%20") + ")\n__Total score:__ **"+totalScore+"**\n__Ranked score:__ **" + ranckedScore + "**\n__Accuracy:__ **" + accuracy + "**", inline=True)
		embed.add_field(name="Hits (300/100/50)", value="**" + hit_300 + "//" + hit_100 + "//" + hit_50 + "**", inline=True)
		embed.add_field(name="Ranks (SS/S/A)", value="**" + rank_SS + "//" + rank_S + "//" + rank_A + "**", inline=True)
	embed.set_footer(icon_url="https://raw.githubusercontent.com/Lemmmy/osusig/master/img/" + mode +".png", text="Results for " + mode + " mode")

	await client.send_message(channel, embed=embed)

async def Beatmap_Embed(channel = None ,title = "Something", diff_overall = "8.5", diff_size = "5", diff_approach = "9", diff_drain = "9", mods = "HDDTHR", difficultyName = "Too hard for u", bpm = "300", max_combo = "1000", total_length = "2:55", drain_lenght = "2:35", difficultyrating="8.52", mode='taiko', beatmapSetId = "602313", beatmapId = "1272259", passcount = 1001, playcount = 12521, approved=True, pp_100 = "350", pp_98 = "293"):

	if approved == BeatmapStatus.ranked:
		ranked = 'Ranked'
	elif approved == BeatmapStatus.approved:
		ranked = 'Approved'
	elif approved == BeatmapStatus.qualified :
		ranked = 'Qualified'
	elif approved == BeatmapStatus.pending :
		ranked = 'Pending'
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

	embed = discord.Embed(title = title + " - [" + difficultyName + "] ▬ " + ranked)
	embed.set_thumbnail(url = "https://b.ppy.sh/thumb/" + beatmapSetId + ".jpg")
	embed.add_field(name = "General", value = "__Bpm:__ **" + bpm + "**\n__Max combo:__ **" + max_combo + "x**\n__Length:__ **" + total_length + " (" + drain_lenght + ")**\n__Stars:__ **" + str(round(difficultyrating, 2)) + "★**\nCS:**" + diff_size + "**  OD:**" + diff_overall + "**  AR:**" + diff_approach + "**  HP:**" + diff_drain + "**")
	embed.add_field(name = "ᅠ", value = "[Thread](https://osu.ppy.sh/beatmapsets/" + beatmapSetId + "#" + modelink + "/" + beatmapId + ") / [Download](https://osu.ppy.sh/d/" + beatmapSetId + ") / [No Video](https://osu.ppy.sh/d/" + beatmapSetId + "n)\n__PP 100%:__ **" + pp_100 + "**\n__PP 98%:__ **" + pp_98 + "**\n__Success rate:__ **" + str(round(float(passcount)/playcount * 100, 0)) + "%**")
	embed.add_field(name = "Mods", value = mods)
	embed.set_footer(icon_url="https://raw.githubusercontent.com/Lemmmy/osusig/master/img/" + mode +".png", text="Results for " + mode + " mode")
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
		print (Red + LogPrefix + message.author.name + " : " + message.content + Color_Off)
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

	for channel in client.private_channels:
		if str(channel.user) == "Renondedju#0204":
			botOwner = channel.user
			break

	await asyncio.sleep(0.1)
	hello = False
	if datetime.now().strftime('%H') == "00" or (set(sys.argv) & set(["refresh"])):
		message = await client.send_message(mainChannel, "<:empty:317951266355544065> Updating stats ...")
		try:
			print('Refreshing users stats ...')
			refresh_all_pp_stats()
			print(" - Done")
			print('Creating new backup ...', end="")
			create_backup()
			print(" Done !")
			await client.edit_message(message, "<:check:317951246084341761> Updating stats ... Done !")
		except:
			await client.edit_message(message, "<:xmark:317951256889131008> Updating stats ... Fail !")
		if not set(sys.argv) & set(["dev"]):
			await client.send_message(mainChannel, "<:online:317951041838514179> Uso!<:Bot:317951180737347587> is now online !")
			await client.change_presence(status=discord.Status('online'), game=discord.Game(name='Osu !'))
			hello = True
	print ('Ready !')
	if (set(sys.argv) & set(["online"])) and hello == False:
		await client.send_message(mainChannel, "<:online:317951041838514179> Uso!<:Bot:317951180737347587> is now online !")
		await client.change_presence(status=discord.Status('online'), game=discord.Game(name='o!help'))
	if set(sys.argv) & set(["dev"]):
		await client.change_presence(status=discord.Status('idle'), game=discord.Game(name='Dev mode'))
 
@client.event
async def on_message(message):
	global api, visible, LogFile

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
			print (main_channel)
			if main_channel == None or main_channel == 0 or main_channel == "0":
				channel = message.channel
			else:
				channel = client.get_server(str(message.server.id)).get_channel(str(main_channel))
				if not commandPrefix + 'dedicated_channel' in message.content:
					await client.send_message(channel, message.author.mention + " i'm here ! I'm only allowed to speak in this channel ^^ There is your command result :")

	if message.content.startswith(commandPrefix + 'test') and (rank in ['ADMIN', 'MASTER']):
		#await client.send_message(message.channel, "Hi ! " + str(message.author) + " my command prefix is '" + commandPrefix + "'")
		parameters = message.content.split(" ")
		embed = discord.Embed(title = "Hi there !", description="**Nice to meet you, I'm Uso!**\nMy command prefix is ``" + commandPrefix + "``\nIf you want to know what am i capable of, try ``" + commandPrefix + "help``\nAdmins : you can mute me if needed by doing ``" + commandPrefix + "mute on``\n\nAdd the bot to your server [Here](https://discordapp.com/oauth2/authorize?client_id=318357311951208448&scope=bot&permissions=0)\nYou can come to my own server to have some help if nedded or even support the devs :D\n➥https://discord.gg/mEeMPyK\n\n:heart::heart::heart:Have fun evryone !:heart::heart::heart:")	
		await client.send_message(channel, embed = embed)

	if message.content.startswith(commandPrefix + 'backup') and (rank in ['MASTER']):
		create_backup()
		await client.send_message(channel, "Backup done")

	if message.content.startswith(commandPrefix + 'log') and (rank in ['MASTER']):
		await Log(message, 0)
		await Log(message, 1)
		await Log(message, 2)

	if message.content.startswith(commandPrefix + 'status') and (rank in ['ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + 'status ', "")
		playmessage = parameters.split(" | ")[0]
		status = parameters.split(" | ")[1]
		await asyncio.sleep(1)
		await client.change_presence(game=discord.Game(name=playmessage), status=discord.Status(status))
		await client.send_message(channel, "Play message set to:``" + playmessage + "``, status set to:``" + status + "``")

	if message.content.startswith(commandPrefix + 'support') and (rank in ['USER', 'ADMIN', 'MASTER']):
		supportfile = open(constants.Paths.supportFile, "r")
		supportString = supportfile.read()
		supportfile.close()
		await client.send_message(channel, supportString)

	if (message.content.startswith(commandPrefix + 'recomandation') or message.content.startswith(commandPrefix + 'r')) and (rank in ['USER', 'ADMIN', 'MASTER']):
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT ppAverage FROM users WHERE DiscordId = ?", (str(message.author.id),))
		try:
			result = cursor.fetchall()[0][0]
		except:
			result = None
		if not(result == None):
			pp_average = int(result*0.97)
			if (pp_average == 0):
				await client.send_message(channel, "Please run the *" + commandPrefix + "update_pp_stats* command to set your stats for the first time in our database")
			else:
				pp_average_fluctuation = pp_average*0.04 - pp_average*0.02

				cursor.execute("Select recomendedBeatmaps From users where DiscordId = ?", (str(message.author.id),))
				alreadyRecomendedId = cursor.fetchall()[0][0]

				if alreadyRecomendedId == None:
					alreadyRecomendedId = "00000"

				cursor.execute("Select * from beatmaps where pp_95 >= ? and pp_95 <= ? and id not in (" + alreadyRecomendedId + ") Limit 1", (str(pp_average-pp_average_fluctuation), str(pp_average+pp_average_fluctuation)))

				recomendedBeatmap = cursor.fetchall()[0]
				url = recomendedBeatmap[0]
				name = recomendedBeatmap[1]
				diff_params = recomendedBeatmap[2]
				pp_100 = recomendedBeatmap[3]
				pp_95 = recomendedBeatmap[4]
				stars = recomendedBeatmap[5]
				combo = recomendedBeatmap[6]
				recomendedId = recomendedBeatmap[7]

				alreadyRecomendedId += "," + str(recomendedId)

				cursor.execute("UPDATE users SET recomendedBeatmaps = ? where DiscordId = ?", (alreadyRecomendedId, str(message.author.id)))
				conn.commit()
				conn.close()

				pp_98, _, _, _, _ = return_simple_beatmap_info(url, " 98%")

				# description = "__100% pp__ : " + str(pp_100) + "\n" + "__98% pp__ : " + str(pp_98) + "\n" + "__95% pp__ : " + str(pp_95) + "\n" + "__Max Combo__ : " + str(combo) + "\n" + "__Stars__ : " + str(stars) + "\n" + str("*" + diff_params.upper() + "*")
				# em = discord.Embed(title=str(name), description=description, colour=0xf44242, url=url)
				# await client.send_message(channel, embed=em)
				results = api.get_beatmaps(beatmap_id=int(recomendedId))
				result = []
				for item in results[0]:
					result.append(item)
				await Beatmap_Embed(channel = channel, title = result[24][1], diff_overall = str(result[9][1]), diff_size = str(result[10][1]), diff_approach = str(result[7][1]), diff_drain = str(result[8][1]), mods = "", difficultyName = str(result[26][1]), bpm = str(result[5][1]), max_combo = str(result[18][1]), total_length = result[25][1], drain_lenght = result[15][1], difficultyrating = result[11][1], mode= result[19][1], beatmapSetId = str(result[4][1]), beatmapId = str(result[3][1]), passcount = result[20][1], playcount = result[21][1], approved=result[0][1], pp_100 = pp_100, pp_98 = pp_98)

				print (recomendedBeatmap)
		else:
			await client.send_message(channel, "Uhh sorry, seems like you haven't linked your osu! account...\nPlease use the command *" + commandPrefix + "link_user 'Your osu username' or 'your osu Id'* to link the bot to your osu account !\nEx. " + commandPrefix + "link_user Renondedju")

	if message.content.startswith(commandPrefix + 'add_beatmap') and (rank in ['ADMIN', 'MASTER']):
		if (message.content.replace(commandPrefix + "add_beatmap ", "") == "" or not(message.content.replace(commandPrefix + "add_beatmap ", "")[0:19] == "https://osu.ppy.sh/")):
			await client.send_message(channel, "Invalid url !")
		else:
			pp_100, pp_95, name, combo, stars, diff_params = return_beatmap_infos(message.content.replace(commandPrefix + "add_beatmap ", ""))
			conn = sqlite3.connect(databasePath)
			cursor = conn.cursor()
			try:
				cursor.execute("""INSERT INTO "beatmaps" (url, name, diff_params, pp_100, pp_95, stars, combo, id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", (message.content.replace(commandPrefix + "add_beatmap ", ""), name, diff_params, pp_100, pp_95, stars, combo, message.content.replace(commandPrefix + "add_beatmap ", "").replace("https://osu.ppy.sh/b/", "").replace("&m=0", "")))
				conn.commit()
				conn.close()
				await client.send_message(message.channel, "Addition done !")
			except sqlite3.IntegrityError:
				await client.send_message(message.channel, "This map is already in the Database !")
	
	if message.content.startswith(commandPrefix + 'add_beats') and (rank in ['MASTER']):

		if str(message.author.id) == constants.Settings.ownerDiscordId:

			await client.send_message(logsChannel, Log(str(message.author), message.content, 0))

			beatmapfile = open(message.content.replace(commandPrefix + 'add_beats ', ""), "r")
			beatmapToProcess = beatmapfile.read().split('\n')
			await client.send_message(message.channel, "<:streaming:317951088646946826> Starting the import of " + str(len(beatmapToProcess)) + " beatmaps")
			await asyncio.sleep(0.1)
			await client.change_presence(status=discord.Status('dnd'), game=discord.Game(name='Processing ...'))

			conn = sqlite3.connect(databasePath)

			await client.send_message(logsChannel, Log(str(message.author), "Ready to add " + str(len(beatmapToProcess)) + " beatmaps to the Database", 1))

			cursor = conn.cursor()
			processed = 1
			done = 0
			infoError = 0
			alreadyExists = 0
			for beatmapUrl in beatmapToProcess:

				print ("Processing " + beatmapUrl + " - " + str(processed) + "/" + str(len(beatmapToProcess)), end="")
				cursor.execute("select url from beatmaps where url = ?", (beatmapUrl,))
				if len(cursor.fetchall()) == 0:
					pp_100, pp_95, name, combo, stars, diff_params = return_beatmap_infos(beatmapUrl, "")
					if not (pp_100 == -1):
						try:
							cursor.execute("""INSERT INTO "beatmaps" (url, name, diff_params, pp_100, pp_95, stars, combo, id) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", (beatmapUrl, name, diff_params, pp_100, pp_95, stars, combo, beatmapUrl.replace("https://osu.ppy.sh/b/", "").replace("&m=0", "")))
							conn.commit()
							print (" - Done")
							await client.send_message(logsChannel, "<:check:317951246084341761> " + beatmapUrl + " ( "+str(processed) + "/" + str(len(beatmapToProcess))  +" ) - Done")
							done += 1
						except sqlite3.IntegrityError:
							print (" - Can't get beatmap infos !")
							await client.send_message(logsChannel, "<:xmark:317951256889131008> " + beatmapUrl + " ( "+str(processed) + "/" + str(len(beatmapToProcess))  +" ) - Can't get beatmap infos !")
							infoError += 1
					else:
						print (" - Can't get beatmap infos !")
						await client.send_message(logsChannel, "<:xmark:317951256889131008> " + beatmapUrl + " ( "+str(processed) + "/" + str(len(beatmapToProcess))  +" ) - Can't get beatmap infos !")
						infoError += 1
				else:
					print (" - Already exists")
					await client.send_message(logsChannel, "<:xmark:317951256889131008> " + beatmapUrl + " ( "+str(processed) + "/" + str(len(beatmapToProcess))  +" ) - Already exists")
					alreadyExists += 1
				processed += 1
			conn.close()

			await client.send_message(logsChannel, Log(str(message.author),  "Successfuly added " + str(len(beatmapToProcess)) + " beatmaps to the database", 1))
			await client.send_message(message.channel, "<:online:317951041838514179> Back online ! - __Done :__ " + str(done) + " , __InfoError :__ " + str(infoError) + " , __Already exists :__ " + str(alreadyExists))
			await asyncio.sleep(0.1)
			await client.change_presence(status=discord.Status('online'), game=discord.Game(name='Osu !'))

		else:
			await client.send_message(logsChannel, Log(str(message.author), "tried to add multiple beatmaps", 1))
			await client.send_message(message.channel, "Sorry, Only Renondedju can do this !")

	if message.content.startswith(commandPrefix + 'mute') and (((rank in ['USER']) and message.channel.permissions_for(message.author).administrator == True) or (rank in ['ADMIN', 'MASTER'])):
		if not (message.server.id == None):
			conn = sqlite3.connect(databasePath)
			cursor = conn.cursor()
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
			conn.close()
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
			conn.close()

	if message.content.startswith(commandPrefix + 'pp') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + "pp ", "")
		url = parameters.split(" ")[0]
		try:
			oppaiParameters = parameters.split(" ")[1:len(parameters.split(" "))]
			oppaiParameters = " ".join(str(x) for x in oppaiParameters)
		except IndexError:
			oppaiParameters = ""

		if (parameters == "" or not(url[0:19] == "https://osu.ppy.sh/")):
			await client.send_message(channel, "Invalid url !")
		else:
			pp_100, pp_95, name, combo, stars, diff_params = return_beatmap_infos(url, oppaiParameters)
			
			if not(pp_100 == -1):

				#add_beatmap_to_queue(url)
				await client.send_message(client.get_server("310348632094146570").get_channel("315166181256593418"), Log(str(client.user.name), "Added " + url + " to beatmap queue", 0))
				description = "__100% pp__ : " + str(pp_100) + "\n" + "__95% pp__ : " + str(pp_95) + "\n" + "__combo max__ : " + str(combo) + "\n" + "__stars__ : " + str(stars) + "\n" + str("*" + diff_params + "*")
				em = discord.Embed(title=str(name), description=description, colour=0xf44242)
				await client.send_message(channel, embed=em)
			else:
				await client.send_message(channel, "Can't get beatmap info...")

	if message.content.startswith(commandPrefix + 'kill') and (rank in ['MASTER']):
		if str(message.author.id) == constants.Settings.ownerDiscordId:
			await client.send_message(logsChannel, Log(str(client.user.name), "Killing the bot !", 0))
			await client.send_message(message.channel, "Alright, killing myself ... bye everyone !")
			client.logout()
			client.close()
			LogFile.close()
			sys.exit("Bot has been shutdown by command correctly !")
		else:
			await client.send_message(logsChannel, Log(str(message.author), "tried to kill the bot !", 1))
			await client.send_message(message.channel, "Sorry, Only Renondedju can do this !")

	if message.content.startswith(commandPrefix + 'user') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.split(' ')
		if len(parameters) == 2:
			parameters.append("osu")
		if len(parameters) != 3:
			await client.send_message(channel, "Wrong usage ! `o!user <your osu username/id/url> <mode>` for more informations, use `o!help`\n*Tip: you can use 'me' instead of your username if you linked your osu account with the bot*")
		else:
			await user(channel, user = parameters[1], mode = parameters[2], discordId= message.author.id)

	if message.content.startswith(commandPrefix + 'link_user') and (rank in ['USER', 'ADMIN', 'MASTER']):
		parameters = message.content.replace(commandPrefix + 'link_user ', '')
		results = get_user(user = parameters, me=False)

		stats = []
		if not (results == []):
			for item in results[0]:
				stats.append(item)
			osuId = stats[16][1]
			osuUsername = stats[17][1]
			userDiscordId = int(message.author.id)
			operationDone = link_user(userDiscordId, osuUsername, osuId, "USER")

			await client.send_message(channel, "Your account has been successfuly " + operationDone + " to ")
			await User_embed(channel, username=str(stats[17][1]), rank_SS=str(stats[6][1]), rank_S=str(stats[5][1]), rank_A=str(stats[4][1]) , pp=str(stats[13][1]), worldRank=str(stats[12][1]), localRank=str(stats[11][1]), country=stats[7][1], playcount=str(stats[10][1]), level=str(stats[9][1]), osuId = str(stats[16][1]), totalScore = str(stats[15][1]), ranckedScore = str(stats[14][1]), accuracy = str(stats[0][1])[0:4]+"%", hit_300 = str(stats[2][1]), hit_100 = str(stats[1][1]), hit_50 = str(stats[3][1]))
			update_pp_message = await client.send_message(channel, "<:empty:317951266355544065> Updating your pp stats for "+ str(message.author) +" ...")

			if update_pp_stats(osuId, message.author.id) == 0:
				await client.edit_message(update_pp_message, "<:check:317951246084341761> Updating your pp stats for "+ str(message.author) +" ... - Done !")

			else:
				await client.edit_message(update_pp_message, "<:xmark:317951256889131008> Updating your pp stats for "+ str(message.author) +" ... - Oops ! Unexpected error.")
		else:
			await client.send_message(channel, "Oups sorry, didn't find this user\n*Try with your osu id instead or the link to your profile*")

	if message.content.startswith(commandPrefix + 'update_pp_stats') and (rank in ['USER', 'ADMIN', 'MASTER']):
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT OsuId FROM users WHERE DiscordId = ?", (str(message.author.id),))
		osuId = cursor.fetchall()[0][0]
		conn.close()
		if not (osuId == None):
			result = update_pp_stats(osuId, message.author.id)
			if result == 0:
				await client.send_message(logsChannel, Log(str(client.user.name), "Succesfuly updated " + str(message.author) + "'s pp stats", 0))
				await client.send_message(channel, "Succesfuly updated " + str(message.author) + "'s pp stats")
			elif result == 1:
				await client.send_message(logsChannel, Log(str(client.user.name), "Wrong osu! id for " + str(message.author), 1))
				await client.send_message(channel, "Wrong osu! id for " + str(message.author) + ". Try to link your account with an osu! account by typing the command *" + commandPrefix + "link_user 'Your osu username'*")
			elif result == 2:
				await client.send_message(logsChannel, Log(str(client.user.name), "Unexpected error for " + str(message.author), 2))
				await client.send_message(channel, "Unexpected error, please try again later or contact Renondedju for more help")
		else:
			await client.send_message(logsChannel, Log(str(client.user.name), "Wrong osu! id for " + str(message.author), 1))
			await client.send_message(channel, "Wrong osu! id for " + str(message.author) + ". Try to link your account with an osu account by typing the command *" + commandPrefix + "link_user 'Your osu username'*")

	if message.content.startswith(commandPrefix + 'help') and (rank in ['USER', 'ADMIN', 'MASTER']):
		if (channel != message.author):
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
	message = args[0]

	if message.content.startswith(commandPrefix) and message.channel.is_private == False and message.content.startswith(commandPrefix + 'mute') == False:
		conn = sqlite3.connect(databasePath)
		cursor = conn.cursor()
		cursor.execute("SELECT state FROM server WHERE serverID = ?", (str(message.server.id),))
		if cursor.fetchall()[0][0] == 'on':
			channel = message.author
		else:
			channel = message.channel

	print (Red + traceback.format_exc() + Color_Off)
	await Log(message, content = "Message:\n" + message.content + "\n\n```" + traceback.format_exc() + "```", logLevel=2)
	await client.send_message(channel, "Oops ! Unexpected error :/\nGo to my personal server to ask for some help if needed !\n<https://discord.gg/mEeMPyK>")

@client.event
async def on_server_join(server):
	conn = sqlite3.connect(databasePath)
	cursor = conn.cursor()
	try:
		cursor.execute("INSERT INTO server (serverID, state) VALUES (?, ?)", (server.id, 'off'))
		conn.commit()
	except sqlite3.IntegrityError:
		print ("Already in database")
	conn.close()
	embed = discord.Embed(title = "Hi there !", description="**Nice to meet you, I'm Uso!**\nMy command prefix is ``" + commandPrefix + "``\nIf you want to know what am i capable of, try ``" + commandPrefix + "help``\nAdmins : you can mute me if needed by doing ``" + commandPrefix + "mute on``\n\nAdd the bot to your server [Here](https://discordapp.com/oauth2/authorize?client_id=318357311951208448&scope=bot&permissions=0)\nYou can come to my own server to have some help if nedded or even support the devs :D\n➥https://discord.gg/mEeMPyK\n\n:heart::heart::heart:Have fun evryone !:heart::heart::heart:")	
	message = await client.send_message(client.get_server(server.id), embed = embed)
	await Log(message, logLevel = 1, thumbnailUrl = server.icon_url, content = "**I've been added to a new server !**\n__Server name :__ **" + str(server.name) + "**\n__Server Id :__ **" + str(server.id) + "**\n__Users :__ **" + str(server.member_count) + "**\n__Owner name :__ **" + str(server.owner.name) + "**")

client.run(constants.Api.discordToken)