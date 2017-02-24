import libvirt 

from xii import error
from xii.component import Component
from xii.need import NeedLibvirt, NeedIO
from xii.util import domain_has_state, domain_wait_state, wait_until_inactive


class ForwardComponent(Component, NeedLibvirt, NeedIO):
    """Define forwards like portforwarding
    TODO: docu!
    """
    short_description="Define forwardings from instance to host"

    ctype = "forward"
    required_attributes = []
    default_attributes = []

    requires = []

    xml_dfn = {'devices': ""}

    def spawn(self):
        pass

    def destroy(self):
        pass

