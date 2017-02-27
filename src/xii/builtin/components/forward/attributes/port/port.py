from xii.validator import Int, List, Dict, VariableKeys

from xii.components.forward import ForwardAttribute


class PortAttribute(ForwardAttribute):
    atype = "port"
    keys = Dict([
        VariableKeys(Dict([
            VariableKeys(Int("8080"), "80", keytype=Int("80"))
            ]), "instance-1")
        ])

    def forwarded_nodes(self):
        return self.settings().keys()

    def get_forwards_for(self, instance):
        tmpl = self.template("node-filter-ref.xml")



    def spawn(self):
        pass

    def _get_nodes(self):
        return self.settings().keys()
