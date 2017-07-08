print("Please wait ...")

import os
import sys
import pyoppai
import time
import sqlite3
from osuapi import *

#"`beatmapId`,`songId`,`diff_params`,`stars`,`combo`,`bpm`,`lenght`,`drain`,`version`,`title`,`creator`,`artist`,`PP_100`,`PP_100_HR`,`PP_100_HD`,`PP_100_DT`,`PP_100_DTHD`,`PP_100_DTHR`,`PP_100_HRHD`,`PP_100_DTHRHD`,`PP_99`,`PP_99_HR`,`PP_99_HD`,`PP_99_DT`,`PP_99_DTHD`,`PP_99_DTHR`,`PP_99_HRHD`,`PP_99_DTHRHD`,`PP_98`,`PP_98_HR`,`PP_98_HD`,`PP_98_DT`,`PP_98_DTHD`,`PP_98_DTHR`,`PP_98_HRHD`,`PP_98_DTHRHD`,`PP_97`,`PP_97_HR`,`PP_97_HD`,`PP_97_DT`,`PP_97_DTHD`,`PP_97_DTHR`,`PP_97_HRHD`,`PP_97_DTHRHD`"

if len(sys.argv) != 3:
	beatmapFileName = input("Name of the file to dowload and extract pp stats: ")
	downloadDirr = input("Dirrectory to download files : ")
	databaseName = input("Name of the database to import the beatmaps : ")
else:
	beatmapFileName = sys.argv[1]
	downloadDirr = sys.argv[2]
	databaseName = sys.argv[3]

downloadDirr = os.getcwd() + "/" + downloadDirr
databaseDirr = os.getcwd() + "/" + databaseName

beatmapsFile = open(os.getcwd() + "/" + beatmapFileName, "r")
beatmaps = beatmapsFile.read().split('\n')
beatmapsFile.close()

beatmapsId = []

conn = sqlite3.connect(databaseDirr)
cursor = conn.cursor()

for i in range(len(beatmaps) - 1):
	id = beatmaps[i].split('/')[len(beatmaps[i].split('/')) - 1]
	beatmapsId.append(int(id.replace("&m=0", "")))

print ("Now downloading " + str(len(beatmapsId)) + " beatmaps to : " + downloadDirr +"/beatmap_id.osu\n")
Dstarted = time.time()

cursor.execute("SELECT beatmapId FROM beatmaps")
alreadyImportedId = cursor.fetchall()
temp = []
for element in alreadyImportedId:
	temp.append(element[0])
alreadyImportedId = temp

done = 0

files = os.listdir(downloadDirr)
for Id in beatmapsId:

	download_speed = done / (time.time() - Dstarted)
	sec = download_speed * (len(beatmapsId) - done)

	remaining_hours = round((sec//3600))
	remaining_min = round((sec - remaining_hours*3600)//60)
	remaining_sec = round(sec - remaining_hours*3600 - remaining_min*60)
	remaining_time = "{:02d}:{:02d}:{:02d}".format(remaining_hours,remaining_min,remaining_sec)

	percents = int(int(str(float(done)/len(beatmapsId)*100).split('.')[0])/float(2))
	print ("\033[94m[" + u"\u2588"*percents + " "*(50 - percents) + "]\033[0m " + str(percents*2) + "% (" + str(done) + "/" + str(len(beatmapsId)) + ")  -  " + remaining_time,end = "")
	sys.stdout.flush()
	print ("\r", end ="")
	
	if (str(Id) + ".osu" in files) or (Id in alreadyImportedId):
		done += 1
	else:
		os.system("sudo curl --silent https://osu.ppy.sh/osu/" + str(Id) + " -o " + downloadDirr + "/" + str(Id) + ".osu")
		done += 1
	
print ("\033[94m[" + u"\u2588"*50+ "]\033[0m 100% (" + str(len(beatmapsId)) + "/" + str(len(beatmapsId)) + ")", end = "")
print ("Done !\n\nExtracting beatmaps stats ...")

Pass = False

def chk(ctx):
	return pyoppai.err(ctx)

BUFSIZE = 2000000

api = OsuApi("fa795ecfa56905e00bb05c175c8371d2548f35f2", connector=ReqConnector())
accuracys = [100, 99, 98, 97]
mods = [pyoppai.nomod, pyoppai.hr, pyoppai.hd, pyoppai.dt, pyoppai.dt | pyoppai.hd, pyoppai.dt | pyoppai.hr, pyoppai.hd | pyoppai.hr, pyoppai.dt | pyoppai.hr | pyoppai.hd]
mods_name = ["Nomod", "HR", "HD", "DT", "HDDT", "HRDT", "HDHR", "HRHDDT"]
beatmapsFileName = []


for beatmap in beatmapsId:
	beatmapsFileName.append(str(beatmap) + ".osu")

started = time.time()

done = 0
for beatmap in beatmapsFileName:

	import_speed = done / (time.time() - started)
	sec = import_speed * (len(beatmapsFileName) - done)

	remaining_hours = round((sec//3600))
	remaining_min = round((sec - remaining_hours*3600)//60)
	remaining_sec = round(sec - remaining_hours*3600 - remaining_min*60)
	remaining_time = "{:02d}:{:02d}:{:02d}".format(remaining_hours,remaining_min,remaining_sec)
	percents = int(int(str(float(done)/len(beatmapsFileName)*100).split('.')[0])/2.0)

	print ("\033[94m[" + u"\u2588"*percents + " "*(50 - percents) + "]\033[0m " + str(percents*2) + "% (" + str(done) + "/" + str(len(beatmapsFileName)) + ") - Remaining time " + remaining_time, end = "")
	sys.stdout.flush()
	print ("\r", end ="")

	data = []
	Pass = False
	if not (int(beatmap.replace(".osu", "")) in alreadyImportedId):
		results = []
		try:
			results = api.get_beatmaps(beatmap_id=int(beatmap.replace(".osu", "")))
		except ValueError:
			Pass = True
		except:
			api = OsuApi("fa795ecfa56905e00bb05c175c8371d2548f35f2", connector=ReqConnector())
			results = api.get_beatmaps(beatmap_id=int(beatmap.replace(".osu", "")))

		if results == []:
			Pass = True
		if Pass == False:
			beatmap_info = {k:v for k, v in results[0]}

			diff_params = "od:" + str(beatmap_info['diff_overall']) + " cs:" + str(beatmap_info['diff_size']) + " ar:" + str(beatmap_info['diff_approach']) + " hp:" + str(beatmap_info['diff_drain'])

			data.append(beatmap_info['beatmap_id'])
			data.append(beatmap_info['beatmapset_id'])
			data.append(diff_params)
			data.append(round(beatmap_info['difficultyrating'], 2))
			data.append(beatmap_info['max_combo'])
			data.append(beatmap_info['bpm'])
			data.append(beatmap_info['total_length'])
			data.append(beatmap_info['hit_length'])
			data.append(beatmap_info['version'])
			data.append(beatmap_info['title'])
			data.append(beatmap_info['creator'])
			data.append(beatmap_info['artist'])
			data.append(str(beatmap_info['approved'] == BeatmapStatus.ranked))

			if beatmap_info['mode'] == OsuMode.osu:
				ctx = pyoppai.new_ctx()
				buf = pyoppai.new_buffer(BUFSIZE)
				b = pyoppai.new_beatmap(ctx)
				for accuracy in accuracys:

					for mod in mods:
						pyoppai.parse(downloadDirr + "/" + beatmap, b, buf, BUFSIZE, False, "/home/pi/DiscordBots/Oppai/oppai/")
						dctx = pyoppai.new_d_calc_ctx(ctx)
						pyoppai.apply_mods(b, mod)
						stars, aim, speed, _, _, _, _ = pyoppai.d_calc(dctx, b)
						acc, pp, aim_pp, speed_pp, acc_pp = pyoppai.pp_calc_acc(ctx, aim, speed, b, accuracy, mod)
						data.append(round(pp))
				if pyoppai.err(ctx) != "Could not find General info":
					try:
						cursor.execute("INSERT INTO beatmaps (beatmapId ,songId ,diff_params ,stars ,combo ,bpm ,lenght ,drain ,version ,title ,creator ,artist ,ranked ,PP_100 ,PP_100_HR ,PP_100_HD ,PP_100_DT ,PP_100_DTHD ,PP_100_DTHR ,PP_100_HRHD ,PP_100_DTHRHD ,PP_99 ,PP_99_HR ,PP_99_HD ,PP_99_DT ,PP_99_DTHD ,PP_99_DTHR ,PP_99_HRHD ,PP_99_DTHRHD ,PP_98 ,PP_98_HR ,PP_98_HD ,PP_98_DT ,PP_98_DTHD ,PP_98_DTHR ,PP_98_HRHD ,PP_98_DTHRHD ,PP_97 ,PP_97_HR ,PP_97_HD ,PP_97_DT ,PP_97_DTHD ,PP_97_DTHR ,PP_97_HRHD ,PP_97_DTHRHD) VALUES(" + "?,"*44 + " ?)", data)
						conn.commit()
					except sqlite3.IntegrityError:
						Pass = True
	done += 1

ended = time.time()
conn.close()

print ("\033[94m[" + u"\u2588"*50 + "]\033[0m 100% (" + str(done) + "/" + str(len(beatmapsFileName)) + ") Remaining time 00:00:00")
print("\nDone !")
import_time = round(ended - started, 2)
print("Imported " + str(len(beatmapsId)) + " beatmaps in " + str(import_time) + " sec (" + str(round(len(beatmapsId)/import_time, 2)) + " beatmap/s)")