import argparse

from xii import command


class StartCommand(command.Command):
    name = ['start', 's']
    help = "load xii definition and start vm's"

    def run(self):
        self.each_component("create")
        self.each_component("finalize")
        self.each_component("spawn")
        self.each_component("start")
        self.finalize()
