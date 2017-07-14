class beatmapinfo(object):
    def __init__(self):
        pass

    def getBeatmapId(self, sender_message):
        """Returns beatmap id from /np"""
        beatmapid=sender_message.split("/b/")
        beatmapid=beatmapid[1].split(" ")
        beatmapid=beatmapid[0]
        return beatmapid

    def getBeatmapStatsFromDb(self, data):
        """Returns a str() dictionnary with beatmap data stocked in database"""
        #0-13, 14-21, 22-29, 30-37, 38-45 = start and end of each line of the list because pls I don't want to waste my time to count anymore
        stats=['beatmapId', 'songId', 'diff_params', 'stars', 'combo', 'bpm', 'length', 'drain', 'version', 'title', 'creator', 'artist', 'ranked',
               'PP_100', 'PP_100_HR', 'PP_100_HD', 'PP_100_DT', 'PP_100_DTHD', 'PP_100_DTHR', 'PP_100_HRHD', 'PP_100_DTHRHD',
               'PP_99', 'PP_99_HR', 'PP_99_HD', 'PP_99_DT', 'PP_99_DTHD', 'PP_99_DTHR', 'PP_99_HRHD', 'PP_99_DTHRHD',
               'PP_98', 'PP_98_HR', 'PP_98_HD', 'PP_98_DT', 'PP_98_DTHD', 'PP_98_DTHR', 'PP_98_HRHD', 'PP_98_DTHRHD',
               'PP_97', 'PP_97_HR', 'PP_97_HD', 'PP_97_DT', 'PP_97_DTHD', 'PP_97_DTHR', 'PP_97_HRHD', 'PP_97_DTHRHD']
        output={}
        for i in range(len(stats)):
            output[stats[i]]=str(data[0][i])
        return output

    def getFlatStatLine(self, data):
        """Returns the powerful /np stats line"""
        title="[https://osu.ppy.sh/beatmapsets/"+data["songId"]+"#osu/"+data["beatmapId"]+" "+data["title"]+" ["+data["version"]+"]] "
        line=[" 97%: "+data["PP_97"], "98%: "+data["PP_98"], "99%: "+data["PP_99"], "100%: "+data["PP_100"]]
        for i in line:
            title+=i+"pp ~ "
        title+=self.secToMin(int(data["length"]))+" ⧗ "
        title+=data["stars"]+" ★ "
        title+=data["bpm"]+"BPM ♪ ~ "
        title+=data["diff_params"].upper()
        return title
        
    def secToMin(self, duration):
        """Returns converted time seconds -> minutes"""
        return str(int(duration)//60) + ":" + str(int(duration)%60)

    def startswith(self, message, startswith):
        """Returns True if message starts with our particle, else False"""
        check=True
        try:
            for i in range(len(startswith)):
                if not startswith[i]==message[i]:
                    check=False
        except IndexError:
            check=False
        return check

