import sqlite3
import random
import sys

# databaseDirr = "/home/pi/DiscordBots/OsuBot/Database.db"

# conn = sqlite3.connect(databaseDirr)
# cursor = conn.cursor()

def recommendation(discordId, conn, ranked = True, mods = "", count = 1, precision = 0.01):

	cursor = conn.cursor()
	cursor.execute("SELECT * FROM users WHERE DiscordId = ?", [int(discordId),])
	request_result = cursor.fetchall()[0]

	pp_average = request_result[5]

	accuracy_average = int(round(request_result[4]))
	accuracy_average = max(97, min(100, accuracy_average))

	if mods == "": 
		mods = select_mod((request_result[6], request_result[7], request_result[8], request_result[9], request_result[10], request_result[11], request_result[12], request_result[13]))
	sys.exit(mods)

	pp_querry = "PP_" + str(accuracy_average) + mods
	recommended_querry =  {"": "NoMod_recommended", "_HR":"HR_recommended", "_HD":"HD_recommended", "_DT":"DT_recommended", "_DTHD":"DTHD_recommended", "_DTHR":"DTHR_recommended", "_HRHD":"HRHD_recommended", "_DTHRHD":"DTHRHD_recommended"}[mods]

	cursor.execute("SELECT " + recommended_querry + " FROM users WHERE discordId = ?", [discordId,])
	recommended = cursor.fetchall()[0][0]

	if recommended == None or recommended == "":
		recommended = "00000"

	beatmaps = []
	while beatmaps == []:
		cursor.execute("SELECT * FROM beatmaps WHERE " + pp_querry + " <= ? AND " + pp_querry + " >= ? AND beatmapId NOT IN (" + recommended + ") AND ranked = ? LIMIT ?", [pp_average + (pp_average * precision), pp_average - (pp_average * precision), str(ranked), count])
		beatmaps = cursor.fetchall()
		precision += 0.01

	recommended_beatmaps = []
	for beatmap in beatmaps:

		diff_params = beatmap[2].split(" ")
		od = diff_params[0].replace("od:", "")
		cs = diff_params[1].replace("cs:", "")
		ar = diff_params[2].replace("ar:", "")
		hp = diff_params[3].replace("hp:", "")

		cursor.execute("SELECT PP_100" + mods + ", PP_98" + mods + " FROM beatmaps WHERE beatmapId = ?", [beatmap[0],])
		pp_results = cursor.fetchall()[0]

		recommended_beatmaps.append((beatmap[9], od, cs, ar, hp, mods.replace("_", ""), beatmap[8], beatmap[5], beatmap[4], beatmap[6], beatmap[7], beatmap[3], beatmap[1], beatmap[0], ranked, pp_results[0], pp_results[1]))

		recommended += "," + str(beatmap[0])

	cursor.execute("UPDATE users SET " + recommended_querry + " = ? WHERE DiscordId = ?", [recommended, discordId])
	conn.commit()

	return recommended_beatmaps

def select_mod(mods_chance):
	mods_name = ("", "_HR", "_HD", "_DT", "_DTHD", "_DTHR", "_HRHD", "_DTHRHD")
	dictionary = dict(zip(mods_name, mods_chance))

	return random.choice([k for k in dictionary for dummy in range(dictionary[k])])

# print (recommendation(82986435782643712, conn))
# conn.close()