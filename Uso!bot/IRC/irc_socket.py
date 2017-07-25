import sys
import traceback
import socket
import sqlite3
import os
import sys
import requests
import json
import discord
from discord.ext import commands as comm
import asyncio
import threading
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import update_stats
import constants
from osuapi import OsuApi, ReqConnector
from irc_commands import commands
from irc_sender import UsoIrc_sender

conn = sqlite3.connect(constants.Paths.beatmapDatabase)
cursor = conn.cursor()

irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

username = constants.Api.IRCusername
password = constants.Api.IRCpassword
RunDiscord = True

print("\nConnecting to irc.ppy.sh:6667")
irc_socket.connect(("irc.ppy.sh", 6667))

irc_socket.send(bytes("PASS " + password + "\n", "UTF-8"))
irc_socket.send(bytes("NICK " + username + "\n", "UTF-8"))
irc_socket.send(bytes("USER " + username + " " + username + " " + username + " " + username + "\n", "UTF-8"))

irc_msg = irc_socket.recv(2048).decode("UTF-8")
irc_msg = irc_msg.strip('\n\r').split("\r\n")

logsList = [] #sender_name, sender_message, date, error

for msg in irc_msg:
	if("464" in msg):
		print("Bad Authorization. Please check your login details")
		sys.exit(0)

print("Connected...\n")

irc_socket.send(bytes("PRIVMSG Renondedju :Connected to bancho !\n", "UTF-8"))
irc_socket.send(bytes("PRIVMSG NaAb_AsD :Connected to bancho !\n", "UTF-8"))

sender = UsoIrc_sender(irc_socket)
irc_commands = commands(irc_socket, conn, sender)
client = comm.Bot(command_prefix='£', command_not_found='No such command !')

@client.command(pass_context=True)
async def reboot(ctx):
	if str(ctx.message.author.id) == constants.Settings.ownerDiscordId:
		await client.send_message(ctx.message.channel, "Rebooting ...")
		os.system('sudo sh /root/UsoBot/IRC/reboot_irc.sh')
	else:
		await client.send_message(ctx.message.channel, "I'm sorry, you can't do that")

async def send_logs():
	global logsList, RunDiscord
	await client.wait_until_ready()
	botOwner = await client.get_user_info(str(constants.Settings.ownerDiscordId))
	channel = client.get_channel(constants.Settings.logsChannelId)
	while not client.is_closed and RunDiscord:
		if logsList:
			log = logsList.pop(0)
			if log[3] == "":
				embed = discord.Embed(description =  'Bancho IRC : ' + log[1])
				embed.set_footer(text = log[2])
				embed.set_author(name = log[0] + " - IRC", icon_url = "https://a.ppy.sh/" + str(log[4]))
				await client.send_message(channel, embed=embed)
			else:
				if len(log[3]) > 1900:
					log[3] = log[3][0:1900] + '\nMessage truncated ...'
				embed = discord.Embed(description = "Message:\n{0}\n\n```{1}```".format(log[1], log[3]), colour = discord.Colour.red())
				embed.set_footer(text = log[2])
				embed.set_author(name = log[0] + " - IRC", icon_url = "https://a.ppy.sh/" + str(log[4]))
				await client.send_message(channel, embed=embed)
				await client.send_message(botOwner, embed=embed)
		await asyncio.sleep(1)
	if not RunDiscord:
		sys.exit(0)

def start_discord_bot():
	client.loop.create_task(send_logs())
	client.run(constants.Api.discordIRCToken)

def log(sender_name, sender_message, osu_id, error = ""):
	date = datetime.now().strftime('%Y/%m/%d at %H:%M:%S')
	log = open("/root/UsoBot/IRC/logs.log", "a")
	log.write(date + "  -  " + sender_name + ": " + sender_message + '\n')
	log.close()
	logsList.append([sender_name, sender_message, date, error, osu_id])

def check_for_stats(osu_name):
	cursor.execute("SELECT osuId FROM users WHERE osuName = ?", (osu_name,))
	osu_id = cursor.fetchall()
	if not osu_id:

		sender.send_message(osu_name, "Hey ! Nice to meet you, it seems to be your first time here ! Remember that this bot is also available on discord [https://discord.gg/Qsw3yD5 server] [https://discordapp.com/oauth2/authorize?client_id=318357311951208448&scope=bot&permissions=8 add the bot to your server] ! Oh and also, if you need a list of the commands avaiable, type : o!help. GL & HF")

		response = requests.get("https://osu.ppy.sh/api/get_user?k=" + constants.Api.osuApiKey + "&u=" + osu_name, verify=True)
		data = response.json()
		osu_id = data[0]["user_id"]

		cursor.execute("INSERT INTO users (osuId, osuName) VALUES (?, ?)", (osu_id, osu_name,))
		conn.commit()
		api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())
		update_stats.update_stats(0, conn, api, username = osu_name)
		return osu_id
	else:
		return osu_id[0][0]

discordThread = threading.Thread(target=start_discord_bot)
discordThread.start()

running = True
while running:
	try:
		# Receive Message
		irc_messages = irc_socket.recv(2048).decode("UTF-8")
		# Strip message
		irc_messages = irc_messages.strip('\r\n').split("\n")
		#print (irc_messages)

		sender.check_buffer()

		for irc_msg in irc_messages:
			#print(irc_msg)
			if ("PRIVMSG" in irc_msg):

				sender_name = irc_msg.split('!', 1)[0][1:]
				sender_message = irc_msg.split('PRIVMSG', 1)[1].split(':', 1)[1]
				private = not "cho@ppy.sh PRIVMSG #osu" in irc_msg.split("!", 1)[1]

				if private:
					#Logs in the console + file

					osu_id = check_for_stats(sender_name)

					print (sender_name + ": " + sender_message)
					log(sender_name, sender_message, osu_id)

					irc_commands.message_check(sender_name, sender_message)

			# Check for Pings
			if ("PING" in irc_msg):
				sender_message = irc_msg.split(' ')[1]
				irc_socket.send(bytes("PONG " + sender_message + "\n", "UTF-8"))
				print ('\x1b[1;32;40m' + "PONG " + sender_message + '\x1b[0m')

	except Exception as e:
		ex_type, ex, tb = sys.exc_info()
		errors = traceback.format_tb(tb)
		err = open("/root/UsoBot/IRC/errors.log", "a")

		date = datetime.now().strftime('%Y/%m/%d at %H:%M:%S')

		errorReport = '\n\n---ERROR REPORT---  ' + date + '\n'
		for error in errors:
			errorReport += error
		errorReport += '{0} : {1}'.format(type(ex).__name__, ex.args)
		errorReport += '\nFrom {0} : {1}'.format(sender_name, sender_message)

		err.write(errorReport)
		print('\x1b[1;31;40m' + errorReport + '\x1b[0m')

		err.close()
		log(sender_name, sender_message, osu_id, error=errorReport)
		sender.send_message(sender_name, "Oops, an error occured ... Don't worry i created a report for the devs to fix this !")
	except KeyboardInterrupt:
		RunDiscord = False
		sys.exit(0)