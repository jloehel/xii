
from xii import attribute, paths
from xii.attribute import Key
from xii.output import show_setting


class IPv4Attribute(attribute.Attribute):
    allowed_components = "network"
    defaults = False

    keys = Key.Bool

    def info(self):
        pass

    def spawn(self):
        pass


attribute.Register.register("ipv4", IPv4Attribute)
