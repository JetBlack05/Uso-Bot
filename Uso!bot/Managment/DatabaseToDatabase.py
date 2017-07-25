import sqlite3

OldDatabaseDirr = "/home/pi/DiscordBots/OsuBot/Database.db"
NewDatabaseDirr = "/home/pi/DiscordBots/OsuBot/beatmaps/NewDatabase.db"

oldConn = sqlite3.connect(OldDatabaseDirr)
oldCursor = oldConn.cursor()

newConn = sqlite3.connect(NewDatabaseDirr)
newCursor = newConn.cursor()


oldCursor.execute("SELECT serverID, state, dedicated_channel FROM server")
servers = oldCursor.fetchall()

for server in servers:
	print(server)
	newCursor.execute("INSERT INTO server (serverID, state, dedicated_channel) VALUES (?, ?, ?)", server)
	newConn.commit()

newConn.close()
oldConn.close()