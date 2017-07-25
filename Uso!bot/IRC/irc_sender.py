import socket
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import constants

class UsoIrc_sender(object):

        def __init__(self, irc_socket, timeout = 1, max_messages = 5, max_interval = 8):
                self.buffer = {}
                self.timeout = timeout
                self.max_messages = max_messages
                self.max_interval = max_interval
                self.irc_socket = irc_socket

        def send_message(self, sender_name, message):
                """Anti spam function to avoid mutes by bancho"""

                if not sender_name in self.buffer:
                        self.buffer[sender_name] = {"messages" : [], "last message sent" : time.time(), "nb message": 1, "timer" : time.time()}
                        self.irc_socket.send(bytes("PRIVMSG " + sender_name + " : " + message + "\n", "UTF-8"))
                        #print("PRIVMSG " + sender_name + " : " + message)
                        #If the user isn't in the buffer, we can dirrectly send the message and store the user into the buffer

                else:
                        now = time.time()
                        self.check_timer(sender_name)

                        #If there is more than <timeout> sec passed since the last message
                        #And the number max of messages isn't reached during the timer
                        #We can send the message
                        if now - self.buffer[sender_name]["last message sent"] >= self.timeout and self.buffer[sender_name]["nb message"] <= self.max_messages:
                                self.irc_socket.send(bytes("PRIVMSG " + sender_name + " : " + message + "\n", "UTF-8"))
                                #print("PRIVMSG " + sender_name + " : " + message)
                                self.buffer[sender_name]["nb message"] += 1
                                self.buffer[sender_name]["last message sent"] = time.time()

                        #Otherwise we store the message into the buffer, ready to be send as soon as possible
                        else:
                                self.buffer[sender_name]["messages"].append(message)

        def check_buffer(self):
                """Send buffered messages as soon as possible"""

                now = time.time()

                for sender_name in list(self.buffer):

                        self.check_timer(sender_name)

                        if now - self.buffer[sender_name]["last message sent"] >= self.timeout and self.buffer[sender_name]["nb message"] <= self.max_messages:
                                try:

                                        message = self.buffer[sender_name]["messages"].pop(0)
                                        self.irc_socket.send(bytes("PRIVMSG " + sender_name + " : " + message + "\n", "UTF-8"))
                                        #print("PRIVMSG " + sender_name + " : " + message)
                                        self.buffer[sender_name]["nb message"] += 1
                                        self.buffer[sender_name]["last message sent"] = now

                                except IndexError:

                                        self.buffer.pop(sender_name)

        def check_timer(self, sender_name):
                """If the timer is > or = to <max_interval> (defalt = 8 sec) then, we can reset the timer and set the nubmer of messages sent during this timer to 0"""
                now = time.time()

                if now - self.buffer[sender_name]["timer"] >= self.max_interval:
                        self.buffer[sender_name]["timer"] = now
                        self.buffer[sender_name]["nb message"] = 0