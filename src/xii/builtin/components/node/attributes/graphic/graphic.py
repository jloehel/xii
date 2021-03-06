from xii.validator import Bool

from xii.components.node import NodeAttribute


class GraphicAttribute(NodeAttribute):
    atype = "graphic"
    keys = Bool(True)
    defaults = True

    def spawn(self):
        if not self.settings():
            return
        xml = self.template('graphic.xml')
        self.add_xml('devices', xml.safe_substitute())
