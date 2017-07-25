import lib.import_beatmap as import_beatmap
import requests
from osuapi import OsuApi, ReqConnector, OsuMod
import sqlite3
import time
import constants

mods = [OsuMod.NoMod, OsuMod.HardRock, OsuMod.Hidden, OsuMod.DoubleTime, OsuMod.DoubleTime | OsuMod.Hidden, OsuMod.DoubleTime | OsuMod.HardRock, OsuMod.HardRock | OsuMod.Hidden, OsuMod.DoubleTime | OsuMod.Hidden | OsuMod.HardRock]

class UserNotInDatabase(Exception):
    pass

def acc(count_300 = 0, count_100 = 0, count_50 = 0, count_miss = 0):
	tolal_hits = count_miss + count_50 + count_100 + count_300
	acc = (count_50 * 50.0 + count_100 * 100.0 + count_300 * 300.0) / (tolal_hits * 300)
	return round(acc * 100, 2)

def print_perfs(stats, osuId, plays):
	print("\n--- Performance for osu id: " + str(osuId) + " --- (top " + str(plays) + " plays)")
	print("PP average: " + str(stats[1]))
	print("Accuracy average: " + str(stats[0]) + "%")
	for index in range(len(mods)):
		print(str(mods[index].longname) + ": " + str(stats[2][index]) + "%")

def update_stats(discordId, conn, api, scores = 20, osuId = 0, username = ""):
	
	cursor = conn.cursor()
	osuId = int(osuId)

	if type(discordId) != int:
		raise ValueError("The discord id provided should be of type int")
	
	acc_average = 0
	pp_average = 0
	mods_perference = [0, 0, 0, 0, 0, 0, 0, 0]
	
	#Get the user_id
	if osuId == 0 and username == "":
		cursor.execute("SELECT * FROM users WHERE DiscordId = ?", [int(discordId)])
		requestResults = cursor.fetchall()
		if requestResults != []:
			osuId = requestResults[0][2]
		else :
			raise UserNotInDatabase("The discord id '" + str(discordId) + "' isn't in the database")

	#Get the user_bests
	apiResults = None
	if username != "":
		apiResults = api.get_user_best(username, limit = scores)
	else:
		apiResults = api.get_user_best(osuId, limit = scores)


	#Beatmaps processing

	bpm = []
	bpm_average = 0

	for beatmap in apiResults:
		beatmap_info = {k:v for k, v in beatmap}
		acc_average += acc(beatmap_info['count300'], beatmap_info['count100'], beatmap_info['count50'], beatmap_info['countmiss'])/scores
		pp_average += beatmap_info['pp']/scores

		try:
			mods_perference[mods.index(beatmap_info['enabled_mods'])] += 100/scores
		except:
			mods_perference[0] += 100/scores

		cursor.execute("SELECT bpm FROM beatmaps WHERE beatmapId = ?", (beatmap_info['beatmap_id'],))
		result = cursor.fetchall()

		multiplicator = 1.0
		if (OsuMod.DoubleTime in beatmap_info['enabled_mods']) or (OsuMod.Nightcore in beatmap_info['enabled_mods']):
			multiplicator *= 1.5
		if OsuMod.HalfTime in beatmap_info['enabled_mods']:
			multiplicator *= 0.75

		if not result:
			beatmap_infos = import_beatmap.get_beatmap_infos(beatmap_info['beatmap_id'])
			import_beatmap.import_beatmap(beatmap_infos)

			print('+ adding beatmap id: {0}'.format(beatmap_info['beatmap_id']))

			bpm.append(round(beatmap_infos['bpm'] * multiplicator))

		else:
			bpm.append(round(result[0][0] * multiplicator))

	if not bpm:
		bpm_average = 0
		bpm = [0]
	else:
		bpm_average = round(sum(bpm, 0.0) / len(bpm))

	#Updating the database
	if osuId != 0:
		cursor.execute("UPDATE users SET accuracy_average = ?, pp_average = ?, NoMod_average = ?, HR_average = ?, HD_average = ?, DT_average = ?, DTHD_average = ?, DTHR_average = ?, HRHD_average = ?, DTHRHD_average = ?, bpm_average = ?, bpm_high = ?, bpm_low = ?  WHERE osuId = ?", [round(acc_average, 2), round(pp_average, 2), mods_perference[0], mods_perference[1], mods_perference[2], mods_perference[3], mods_perference[4], mods_perference[5], mods_perference[6], mods_perference[7], bpm_average, max(bpm), min(bpm), int(osuId)])
	else:
		cursor.execute("UPDATE users SET accuracy_average = ?, pp_average = ?, NoMod_average = ?, HR_average = ?, HD_average = ?, DT_average = ?, DTHD_average = ?, DTHR_average = ?, HRHD_average = ?, DTHRHD_average = ?, bpm_average = ?, bpm_high = ?, bpm_low = ? WHERE osuName = ?", [round(acc_average, 2), round(pp_average, 2), mods_perference[0], mods_perference[1], mods_perference[2], mods_perference[3], mods_perference[4], mods_perference[5], mods_perference[6], mods_perference[7], bpm_average, max(bpm), min(bpm), username])
	conn.commit()

	return round(acc_average, 2), round(pp_average, 2), mods_perference

def update_all_stats(conn, cursor):
	cursor.execute("SELECT osuId FROM users")
	requestResults = cursor.fetchall()
	for osu_id in requestResults:
		print(osu_id[0], end = " ")
		api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())
		try:
			update_stats(0, conn, api, osuId = osu_id[0])
		except:
			update_stats(0, conn, api, osuId = osu_id[0])
		print ("Done")