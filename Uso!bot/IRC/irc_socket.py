import sys
import socket
import time
import sqlite3
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants
import requests
import json
from osuapi import OsuApi, ReqConnector

from irc_sender import UsoIrc_sender
from irc_beatmapinfos import beatmapinfo
from userlink_key import userlink
import update_stats

conn = sqlite3.connect(constants.Paths.beatmapDatabase)
cursor = conn.cursor()

api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())

irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

username = constants.Api.IRCusername
password = constants.Api.IRCpassword

print("\nConnecting to irc.ppy.sh:6667")
irc_socket.connect(("irc.ppy.sh", 6667))

irc_socket.send(bytes("PASS " + password + "\n", "UTF-8"))
irc_socket.send(bytes("NICK " + username + "\n", "UTF-8"))
irc_socket.send(bytes("USER " + username + " " + username + " " + username + " " + username + "\n", "UTF-8"))

irc_msg = irc_socket.recv(2048).decode("UTF-8")
irc_msg = irc_msg.strip('\n\r').split("\r\n")

for msg in irc_msg:
	if("464" in msg):
		print("Bad Authorization. Please check your login details in the _settings file.")
		sys.exit(0)

print("Connected...\n")

irc_socket.send(bytes("PRIVMSG Renondedju :Connected to bancho !\n", "UTF-8"))
irc_socket.send(bytes("JOIN #osu\n", "UTF-8"))

sender = UsoIrc_sender(irc_socket)
bmData = beatmapinfo()
linkacc = userlink(conn)

def check_for_stats(osu_name):
	cursor.execute("SELECT * FROM users WHERE osuName = ?", (osu_name,))
	if not cursor.fetchall():

		sender.send_message(osu_name, "Hey ! Nice to meet you , it seems to be your first time here ! Please wait a second ... If you need a list of the commands avaiable, type : o!help. GL & HF")

		response = requests.get("https://osu.ppy.sh/api/get_user?k=" + constants.Api.osuApiKey + "&u=" + osu_name, verify=True)
		data = response.json()
		osu_id = data[0]["user_id"]

		cursor.execute("INSERT INTO users (osuId, osuName) VALUES (?, ?)", (osu_id, osu_name,))
		conn.commit()
		update_stats.update_stats(0, conn, api, username = osu_name)


running = True

while running:
	# Receive Message
	irc_messages = irc_socket.recv(2048).decode("UTF-8")
	# Strip message
	irc_messages = irc_messages.strip('\r\n').split("\n")
	#print (irc_messages)

	for irc_msg in irc_messages:
		#print(irc_msg)
		if ("PRIVMSG" in irc_msg):

			sender_name = irc_msg.split('!', 1)[0][1:]
			sender_message = irc_msg.split('PRIVMSG', 1)[1].split(':', 1)[1]
			private = not "cho@ppy.sh PRIVMSG #osu" in irc_msg.split("!", 1)[1]

			if private:

				check_for_stats(sender_name)

				if "ACTION is listening to" in sender_message:#/np
					beatmapid=bmData.getBeatmapId(sender_message)
					cursor.execute("SELECT * FROM beatmaps WHERE beatmapId = ?", (str(beatmapid),))
					data=cursor.fetchall()
					if not data:
						sender.send_message(sender_name, "Sorry, this beatmap isn't in my database for now :/")
					else:
						sender.send_message(sender_name, bmData.getFlatStatLine(bmData.getBeatmapStatsFromDb(data)))

				if sender_message.startswith("o!help"):#Send simple help
					sender.send_message(sender_name, "Here's the list of all the commands you can use with me ! : /np ~ o!help ~ There is more coming !")

				if send_message.startswith("o!kill"):
					if sender_name == "Renondedju":
						sender.send_message(sender_name, "Shuting down .."
						sys.exit()

				if sender_message.startswith("pass"):
					key = sender_message.split(" ")[1].replace(" ", "")
					response = requests.get("https://osu.ppy.sh/api/get_user?k=" + constants.Api.osuApiKey + "&u=" + sender_name, verify=True)

					data = response.json()
					osu_id = data[0]["user_id"]

					try:
						linkacc.link_account(osu_id, key, sender_name)
						sender.send_message(sender_name, "The link between Discord and osu! is done !")

					except ValueError:
						sender.send_message(sender_name, "The key you tried to use doesn't exists or expired ! Ask for another one on discord")

					except KeyError:
						sender.send_message(sender_name, "Sorry, there is no link_user request for this account now :/ If you want to link your discord with osu, go to discord and send me : o!link_user yourUsername")

				print ('\x1b[1;31;40m' + sender_name, end = " -> ")
				print (sender_message + '\x1b[0m')
			
		# Check for Pings
		if ("PING" in irc_msg):
			sender_message = irc_msg.split(' ')[1]
			irc_socket.send(bytes("PONG " + sender_message + "\n", "UTF-8"))
			print ('\x1b[1;32;40m' + "PONG " + sender_message + '\x1b[0m')