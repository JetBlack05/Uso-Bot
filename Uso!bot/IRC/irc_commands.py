import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants
from irc_sender import UsoIrc_sender
from irc_beatmapinfos import beatmapinfo
from userlink_key import userlink
import lib.import_beatmap as import_beatmap
import recommendation
import inspect
import sqlite3
import requests
import json

class commands(object):
        """Class used to stock all the IRC commands, to make irc_socket cleaner"""

        def __init__(self, irc_socket, conn, irc_sender):
                self.sender = irc_sender
                self.bdata = beatmapinfo()
                self.conn = conn
                self.cursor = conn.cursor()
                self.link_acc = userlink(conn)
                #self.np_dict = {}##BETA

##BETA
##        def cmd_with(self, sender_name, sender_message):
##                """Shows stats about beatmaps with different mods, accuracy and misses"""
##                if not sender_name in self.np_dict:
##                        return self.sender.send_message(sender_name, "In order to use " + constants.Settings.commandPrefix + "with you have to /np a beatmap before")
##                mods_line = sender_message.strip().split(constants.Settings.commandPrefix+"with ")[1]#replace with with command name
##                mods_selected = self.bdata.mods_parser(mods_line)
##                if mods_selected is False:#If wrong mods
##                        return self.sender.send_message(sender_name, "Wrong")
##                else:#If correct mods returns the mod list
##                        pass

        def cmd_help(self, sender_name, sender_message):
                """Sends all IRC commands available, also gives details about a command with o!help command_name"""
                if sender_message.strip() == "o!help /np":
                        command = "/np"
                else:
                        command = sender_message.replace("o!help", "", 1).strip(" ")
                        if command.startswith("o!"):
                                command = command.strip("o!")
                if command:
                        if command == "/np":
                                cmd = getattr(self, "cmd_np", None)
                        else:
                                cmd = getattr(self, 'cmd_' + command, None)
                        if cmd:
                                return self.sender.send_message(sender_name, "{}".format(str(cmd.__doc__), command_prefix = constants.Settings.commandPrefix))
                        else:
                                return self.sender.send_message(sender_name, "No such command : "+command)
                else:
                        help_message = "Here are all the commands available ! : "
                        commands = []
                        for attributes in dir(self):
                                if attributes.startswith("cmd_np"):
                                        commands.append("/np")
                                elif attributes.startswith("cmd_kill"):
                                        pass
                                elif attributes.startswith("cmd_"):
                                        commands.append("{}{}".format(constants.Settings.commandPrefix, attributes.replace("cmd_", "").lower()))
                        help_message+=" ~ ".join(commands)
                        help_message+=" ~ You can use o!help command_name to get infos about a specific command and its arguments : [] are optional arguments; () are mandatory arguments"
                        self.sender.send_message(sender_name, help_message)

        def cmd_kill(self, sender_name):
                """Kills the IRC bot, forcing it to shutdown"""
                if sender_name == "Renondedju":
                        self.sender.send_message(sender_name, "Shuting down ..")
                        sys.exit(0)

        def cmd_np(self, sender_name, sender_message):
                """A magic line that shows no mod stats about the user's beatmap"""
                beatmapid = self.bdata.getBeatmapId(sender_message)
                self.cursor.execute("SELECT * FROM beatmaps WHERE beatmapId = ?", (str(beatmapid),))
                data = self.cursor.fetchall()
                if not data:
                        beatmap_info = import_beatmap.get_beatmap_infos(beatmapid)
                        length = str(int(beatmap_info['total_length'])//60) + ":" + str(int(beatmap_info['total_length'])%60)
                        description = "97%: " + str(beatmap_info['pp_97_Nomod']) + "pp ~ 98%: " + str(beatmap_info['pp_98_Nomod']) + "pp ~ 99%: " + str(beatmap_info['pp_99_Nomod']) + "pp ~ 100%: " + str(beatmap_info['pp_100_Nomod']) + "pp ~ "
                        description += length + '⧗ ' + str(round(beatmap_info['difficultyrating'], 2)) + "★ " + str(beatmap_info['bpm']) + "BPM ♪ ~ OD:" + str(beatmap_info['diff_overall']) + " CS:" + str(beatmap_info['diff_size']) + " AR:" + str(beatmap_info['diff_approach'])
                        description += " %s" % ("(if ranked)" if not str(beatmap_info['approved'])=="<BeatmapStatus.ranked: 1>" else "")
                        print (beatmap_info['approved'])
                        print(str(beatmap_info['approved'])=="<BeatmapStatus.ranked: 1>")
                        self.sender.send_message(sender_name, description)
                else:
                        self.sender.send_message(sender_name, self.bdata.getFlatStatLine(self.bdata.getBeatmapStatsFromDb(data)))

        def key_check(self, sender_name, sender_message):
                """In order to check key to link discord/osu accounts"""
                key = sender_message.split(" ")[1].replace(" ", "")
                response = requests.get("https://osu.ppy.sh/api/get_user?k=" + constants.Api.osuApiKey + "&u=" + sender_name, verify=True)

                data = response.json()
                osu_id = data[0]["user_id"]

                try:
                        self.link_acc.link_account(osu_id, key, sender_name)
                        self.sender.send_message(sender_name, "The link between Discord and osu! is done !")

                except ValueError:
                        self.sender.send_message(sender_name, "The key you tried to use doesn't exists or expired ! Ask for another one on discord")

                except KeyError:
                        self.sender.send_message(sender_name, "Sorry, there is no link_user request for this account now :/ If you want to link your discord with osu, go to discord and send me : o!link_user yourUsername")

        def cmd_r(self, sender_name, sender_message):
                """Usage : o!r [/pp (0,1000)] [/count (1,5)] [/ranked (True/False)] [/mods (HD,DT,HR)] [/acc (97,100)] [/bpm (0,1000)] ex.: o!r /pp 100 /bpm 170 /mods DTHD"""
                parameters = sender_message.split("/")
                if len(sender_message) > 3 and len(parameters) == 1:
                	self.sender.send_message(sender_name, self.cmd_r.__doc__)
                	return

                count = 1
                mods = None
                ranked = True
                Continue = True
                acc = None
                bpm = None
                pp = None

                for parameter in parameters:
                        if parameter == "":
                                sender.send_message(sender_name, "You need to specify a parameter behind a '/' !\n*/c -> count, /pp -> pp, /r -> ranked, /m -> mods, /a -> accuracy*")
                                Continue = False

                        elif parameter[0] == "p":
                                try:
                                        pp = max(min(int(parameter.replace("p", "").replace("pp", "").replace(" ", "")), 1000), 0)
                                        mods = ""
                                        acc = 100
                                except ValueError:
                                        Continue = False
                                        self.sender.send_message(sender_name, "The parameter /pp require a number (between 0 and 1000)")

                        elif parameter[0] == "c":
                                try:
                                        count = max(min(int(parameter.replace("count", "").replace("c", "").replace(" ", "")), 5), 1)
                                except ValueError:
                                        Continue = False
                                        self.sender.send_message(sender_name, "The parameter /c *(count)* require a number (between 1 and 5)")

                        elif parameter[0] == "r":
                                ranked = parameter.replace("ranked", "").replace("r", "").replace(" ", "").lower() == "true"

                        elif parameter[0] == "m":
                                temp_mods = parameter.replace("mods", "").replace("mod", "").replace("m", "").replace(" ", "").upper()
                                mods = ""
                                if "nomod" in temp_mods.lower():
                                        mods = ""
                                if "DT" in temp_mods:
                                        mods += "DT"
                                if "HR" in temp_mods:
                                        mods += "HR"
                                if "HD" in temp_mods:
                                        mods += "HD"
                                if mods != "":
                                        mods = "_" + mods

                        elif parameter[0] == "a":
                                try:
                                        acc = max(min(round(float(parameter.replace("accuracy", "").replace("acc", "").replace("a", "").replace(" ", ""))), 100), 97)
                                except ValueError:
                                        Continue = False
                                        self.sender.send_message(sender_name, "The parameter /a *(accuracy)* require a number (between 97 and 100)")
                        elif parameter[0] == "b":
                                try:
                                        bpm = max(0, min(1000, int(parameter.replace("bpm", "").replace("b", "").replace(" ", ""))))
                                except ValueError:
                                        Continue = False
                                        self.sender.send_message(sender_name, "The parameter /b *(bpm)* require a number (between 0 and 1000)")

                if Continue:
                        self.cursor.execute("SELECT * FROM users WHERE osuName = ?", [sender_name])
                        result = self.cursor.fetchall()[0]
                        #title, od, cs, ar, hp, mods, version, bpm, combo, length, drain, stars, song_id, beatmap_id, ranked, pp 100, pp 99, pp 98, author
                        
                        for r in recommendation.recommendation(0, self.conn, count = count, mods = mods, ranked = ranked, acc = acc, pp = pp, bpm = bpm, osu_id = int(result[2])):

                                diff_params = 'OD:' + str(r[1]) + ' CS:' + str(r[2]) + ' AR:' + str(r[3]) + ' HP:' + str(r[4])
                                download_link = "[https://osu.ppy.sh/b/" + str(r[13]) + " " + r[0] +" ["+ r[6] +"]] "
                                mods = ''
                                if r[5] != '':
                                        mods = '+' + r[5]
                                pp_stats = ' ~ 98%: ' + str(r[17]) + 'pp ~ 99%: ' + str(r[16]) + 'pp ~ 100%: ' + str(r[15]) + 'pp '

                                length = ' ~ ' + str(int(r[9])//60) + ":" + str(int(r[9])%60) + '⧗ '
                                stars = str(r[11]) + '★ '
                                bpm = str(r[7]) + 'BPM ♪ ~ '
                                
                                self.sender.send_message(sender_name, download_link + mods + pp_stats + length + stars + bpm + diff_params)

        def message_check(self, sender_name, sender_message):
                if not "ACTION is listening to" in sender_message and not sender_message.startswith(constants.Settings.commandPrefix) and not sender_message.startswith("pass"):
                        return

                command, *args = sender_message.split()
                command = command[len(constants.Settings.commandPrefix):].lower().strip()

                if "ACTION is listening to" in sender_message:
                        handler = getattr(self, "cmd_np", None)
                elif sender_message.startswith("pass"):
                        handler = getattr(self, "key_check", None)
                else:
                        handler = getattr(self, "cmd_%s" % command, None)

                if not handler:
                        return self.sender.send_message(sender_name, "Oops ! This command doesn't exist, if you want the list of commands, please type o!help")
                else:
                        argspec = inspect.signature(handler)
                        params = argspec.parameters.copy()

                        handler_kwargs={}
                        if params.pop('sender_name', None):
                                handler_kwargs['sender_name'] = sender_name
                        if params.pop('sender_message', None):
                                handler_kwargs['sender_message'] = sender_message
                        for key, param in list(params.items()):
                                if not args and param.default is not inspect.Parameter.empty:
                                        params.pop(key)
                                        continue
                                if args:
                                        arg_value = args.pop(0)
                                        handler_kwargs[key] = arg_value
                                        params.pop(key)
                        response = handler(**handler_kwargs)

