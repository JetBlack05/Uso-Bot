import pyoppai
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants
from osuapi import *
import sqlite3

def chk(ctx):
	err = pyoppai.err(ctx)
	if err:
		print(err)

def download_beatmap(beatmap_id):
	local_beatmap = os.listdir(constants.Paths.beatmapsDownloadsPermanent)
	if not str(beatmap_id) + ".osu" in local_beatmap:
		os.system("sudo curl --silent https://osu.ppy.sh/osu/" + str(beatmap_id) + " -o " + constants.Paths.beatmapsDownloadsPermanent + "/" + str(beatmap_id) + ".osu")

def get_pp_infos(beatmap_id):
	BUFSIZE = 2000000

	accuracys = [100, 99, 98, 97]
	mods = [pyoppai.nomod, pyoppai.hr, pyoppai.hd, pyoppai.dt, pyoppai.dt | pyoppai.hd, pyoppai.dt | pyoppai.hr, pyoppai.hd | pyoppai.hr, pyoppai.dt | pyoppai.hr | pyoppai.hd]
	mods_name = ["Nomod", "HR", "HD", "DT", "HDDT", "HRDT", "HDHR", "HRHDDT"]

	pp_results = {}

	ctx = pyoppai.new_ctx()
	buf = pyoppai.new_buffer(BUFSIZE)
	b = pyoppai.new_beatmap(ctx)

	err = pyoppai.err(ctx)
	if err:
		print(err)
		pass
	for accuracy in accuracys:
		i = 0
		for mod in mods:
			pyoppai.parse(constants.Paths.beatmapsDownloadsPermanent + "/" + str(beatmap_id) + ".osu", b, buf, BUFSIZE, False, constants.Paths.beatmapsDownloadsPermanent)
			dctx = pyoppai.new_d_calc_ctx(ctx)
			pyoppai.apply_mods(b, mod)
			stars, aim, speed, _, _, _, _ = pyoppai.d_calc(dctx, b)
			_, pp, _, _, _ = pyoppai.pp_calc_acc(ctx, aim, speed, b, accuracy, mod)

			err = pyoppai.err(ctx)
			if err:
				print(err)
				pass

			pp_results["pp_" + str(accuracy) + "_" + mods_name[i]] = round(pp)
			i += 1

	return pp_results

def get_beatmap_infos(beatmap_id):
	download_beatmap(beatmap_id)

	api = OsuApi(constants.Api.osuApiKey, connector=ReqConnector())
	beatmap_infos = api.get_beatmaps(beatmap_id=beatmap_id)

	beatmap_infos = {k:v for k, v in beatmap_infos[0]}

	pp_infos = get_pp_infos(beatmap_id)

	beatmap_infos.update(pp_infos)

	return beatmap_infos

def import_beatmap(beatmap_info):
	conn = sqlite3.connect(constants.Paths.beatmapDatabase)
	cursor = conn.cursor()

	diff_params = "od:" + str(beatmap_info['diff_overall']) + " cs:" + str(beatmap_info['diff_size']) + " ar:" + str(beatmap_info['diff_approach']) + " hp:" + str(beatmap_info['diff_drain'])

	data = []
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
	data.append(beatmap_info['pp_100_Nomod'])
	data.append(beatmap_info['pp_100_HR'])
	data.append(beatmap_info['pp_100_HD'])
	data.append(beatmap_info['pp_100_DT'])
	data.append(beatmap_info['pp_100_HDDT'])
	data.append(beatmap_info['pp_100_HRDT'])
	data.append(beatmap_info['pp_100_HDHR'])
	data.append(beatmap_info['pp_100_HRHDDT'])
	data.append(beatmap_info['pp_99_Nomod'])
	data.append(beatmap_info['pp_99_HR'])
	data.append(beatmap_info['pp_99_HD'])
	data.append(beatmap_info['pp_99_DT'])
	data.append(beatmap_info['pp_99_HDDT'])
	data.append(beatmap_info['pp_99_HRDT'])
	data.append(beatmap_info['pp_99_HDHR'])
	data.append(beatmap_info['pp_99_HRHDDT'])
	data.append(beatmap_info['pp_98_Nomod'])
	data.append(beatmap_info['pp_98_HR'])
	data.append(beatmap_info['pp_98_HD'])
	data.append(beatmap_info['pp_98_DT'])
	data.append(beatmap_info['pp_98_HDDT'])
	data.append(beatmap_info['pp_98_HRDT'])
	data.append(beatmap_info['pp_98_HDHR'])
	data.append(beatmap_info['pp_98_HRHDDT'])
	data.append(beatmap_info['pp_97_Nomod'])
	data.append(beatmap_info['pp_97_HR'])
	data.append(beatmap_info['pp_97_HD'])
	data.append(beatmap_info['pp_97_DT'])
	data.append(beatmap_info['pp_97_HDDT'])
	data.append(beatmap_info['pp_97_HRDT'])
	data.append(beatmap_info['pp_97_HDHR'])
	data.append(beatmap_info['pp_97_HRHDDT'])
	
	try:
		cursor.execute("INSERT INTO beatmaps (beatmapId ,songId ,diff_params ,stars ,combo ,bpm ,lenght ,drain ,version ,title ,creator ,artist ,ranked ,PP_100 ,PP_100_HR ,PP_100_HD ,PP_100_DT ,PP_100_DTHD ,PP_100_DTHR ,PP_100_HRHD ,PP_100_DTHRHD ,PP_99 ,PP_99_HR ,PP_99_HD ,PP_99_DT ,PP_99_DTHD ,PP_99_DTHR ,PP_99_HRHD ,PP_99_DTHRHD ,PP_98 ,PP_98_HR ,PP_98_HD ,PP_98_DT ,PP_98_DTHD ,PP_98_DTHR ,PP_98_HRHD ,PP_98_DTHRHD ,PP_97 ,PP_97_HR ,PP_97_HD ,PP_97_DT ,PP_97_DTHD ,PP_97_DTHR ,PP_97_HRHD ,PP_97_DTHRHD) VALUES(" + "?,"*44 + " ?)", data)
		conn.commit()
	except sqlite3.IntegrityError:
		pass
	conn.close()