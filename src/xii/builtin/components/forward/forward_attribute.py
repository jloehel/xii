from abc import ABCMeta, abstractmethod
from xii import attribute


class ForwardAttribute(attribute.Attribute):
    __meta__ = ABCMeta

    @abstractmethod
    def used_nodes(self):
        pass

    @abstractmethod
    def forward_for(self, instance):
        pass

    def add_xml(self, xml):
        self.component().add_xml(xml)
