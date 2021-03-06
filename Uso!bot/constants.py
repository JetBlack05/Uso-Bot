# -*- coding: utf-8 -*-
"""
This is a setting file created by Renondedju

Evry parameters written in this file are private and secret !
"""

class Api:
	osuApiKey = "" #Osu api key (can be found here : https://osu.ppy.sh/p/api#)
	discordToken = "" #Discord bot token (https://discordapp.com/developers/applications/me)
	discordIRCToken = "" #Discord-IRC bot token
	IRCusername = "" #IRC username
	IRCpassword = "" #IRC password

class Paths:
	workingDirrectory = "/root/UsoBot/" #The full path to OsuBot.py
	beatmapDatabase = workingDirrectory + "Database.db" #Beatmaps database full path
	beatmapsDownloadsPermanent = workingDirrectory + "beatmaps/permanent" #Full path to the permanants downloads (unused)
	managmentFiles = workingDirrectory + "Managment" #Full path to the managment files (unused)
	logsFile = workingDirrectory + "logs.txt" #Full path to the log file
	helpMasterFile = workingDirrectory + "helpFiles/helpMASTER.txt"
	helpAdminFile = workingDirrectory + "helpFiles/helpADMIN.txt"
	helpUserFile = workingDirrectory + "helpFiles/helpUSER.txt"
	backupDirrectory = workingDirrectory + "DatabaseBackup/"

class Settings:
	commandPrefix = "o!" #Commant prefix required to trigger the bot
	mainServerID = "310348632094146570" #Main announce server of the bot
	mainChannelId = "310348632094146570" #Main channel of the bot's server
	logsChannelId = "315166181256593418" #Logs channel of the bot's server
	ownerDiscordId = "213262036069515264" #Discord Id of the bot owner
	inviteLink = "https://discord.gg/Qsw3yD5" #Official invite link to the dev server