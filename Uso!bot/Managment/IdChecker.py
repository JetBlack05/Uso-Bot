import sqlite3

conn = sqlite3.connect('/home/pi/DiscordBots/OsuBot/Database.db')
cursor = conn.cursor()
cursor.execute("SELECT * from beatmaps")
beatmaps = cursor.fetchall()

for beatmap in beatmaps:
	url = beatmap[0]
	Id = url.replace("https://osu.ppy.sh/b/", "").replace("&m=0", "")
	print (Id, end= " ")
	cursor.execute("UPDATE beatmaps SET id = '" + str(Id) + "' WHERE url = '" + url + "'")
	conn.commit()
	print ("- Done")

conn.close()