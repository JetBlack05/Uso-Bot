# -*- coding: utf-8 -*- 

import sqlite3
import sys

Color_Off='\x1b[0m'
Red='\x1b[1;31;40m'
Green='\x1b[1;32;40m'

if len(sys.argv) != 3:
	print (Red + "Please pass 2 arguments (first is database path, second is output file path)" + Color_Off)
else:
	outputfile = open(sys.argv[2], "a")
	conn = sqlite3.connect(sys.argv[1])
	cursor = conn.cursor()

	try:
		cursor.execute("SELECT url FROM beatmaps")
		beatmaps = cursor.fetchall()
		conn.close()
		for beatmap in beatmaps:
			outputfile.write(beatmap[0].encode("ascii", "ignore").replace("/b/", "/osu/") + "\n")

		print (Green + "Succesfuly processed " + str(len(beatmaps)) + " beatmaps" + Color_Off)
	except:
		print (Red + "Error ..." + Color_Off)