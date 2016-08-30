import os
import sys

from abc import ABCMeta, abstractmethod


class colors:
    TAG = '\033[0m'
    NORMAL = '\033[37m'
    CLEAR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WARN = '\033[91m'
    SUCCESS = '\033[34m'


def width():
    _, columns = os.popen('stty size', 'r').read().split()
    return int(columns)


def warn(msg, tag="[xii]"):
    output = "{} {}".format(tag, msg)
    print(colors.WARN + colors.BOLD + output + colors.CLEAR)


class UI():

    def clear(self):
        sys.stdout.write("\033[2K")
        sys.stdout.flush()

    def up(self, n):
        if n < 1:
            return
        sys.stdout.write("\033[{}F".format(n))
        sys.stdout.flush()

    def tprint(self, tag, msg, wrap=None):
        stop = 35
        fill = stop - len(tag)
        line = "{} {}: {}".format(tag, "." * fill, msg)

        if wrap:
            line = wrap + line + colors.CLEAR
        print(line)


class HasOutput:
    __meta__ = ABCMeta

    @abstractmethod
    def get_ui(self):
        pass

    def say(self, msg):
        self.get_ui().tprint(self._generate_tag(),
                             msg,
                             colors.NORMAL)
    def add_say(self, msg, indent=2):
        self.say("{}::{}".format(" " * indent, msg))

    def counted(self, i, msg):
        tag = "{}[#{}]".format(self._generate_tag(), i)
        self.get_ui().tprint(tag,
                             msg,
                             colors.NORMAL)

    def warn(self, msg):
        self.get_ui().tprint(self._generate_tag(),
                             msg,
                             colors.WARN + colors.BOLD)

    def success(self, msg):
        self.get_ui().tprint(self._generate_tag(),
                             msg,
                             colors.SUCCESS + colors.BOLD)

    def _generate_tag(self):
        tag = ""
        for ident in self.full_name():
            tag += "[" + ident + "]"
        return tag
