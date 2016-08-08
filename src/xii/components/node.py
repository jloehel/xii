import libvirt

from xii.component import Component
from xii.need_libvirt import NeedLibvirt
from xii.need_io import NeedIO

from xii import component, paths, error
from xii.util import domain_has_state, domain_wait_state, wait_until_inactive


class NodeComponent(Component, NeedLibvirt):
    entity = "node"

    requires = ["image"]
    defaults = ["network", "hostname"]

    xml_dfn = {'devices': ""}

    def add_xml(self, section, xml):
        self.xml_dfn[section] += "\n" + xml

    def start(self):
        domain = self.get_domain(self.name, raise_exception=False)

        if not domain:
            domain = self._spawn_domain()

        if domain.isActive():
            self.say("is already started")
            return

        self.say("starting {}...".format(self.ident()))
        self.childs_run("start")
        domain.create()
        self.success("started!")

    def stop(self, force=False):
        domain = self.get_domain(self.name)

        self.childs_run("stop")
        self._stop_domain(domain, force)

    def destroy(self):
        self.say("destroying...")
        domain = self.get_domain(self.name)

        if domain_has_state(domain, libvirt.VIR_DOMAIN_PAUSED):
            domain.resume()

        if domain_has_state(domain, libvirt.VIR_DOMAIN_RUNNING):
            self._stop_domain(domain, force=True)

        if domain.isActive():
            raise error.Bug("Could not remove running "
                            "domain {}".format(self.ident()))

        self.childs_run("destroy")
        domain.undefine()
        self.success("removed!")

    def suspend(self):
        self.say("suspending...")
        domain = self.get_domain(self.name)

        if domain_has_state(domain, libvirt.VIR_DOMAIN_PAUSED):
            self.warn("is already suspended")
            return

        domain.suspend()

        if not domain_wait_state(domain, libvirt.VIR_DOMAIN_PAUSED):
            self.warn("failed to suspend")
            return
        self.success("suspended!")

    def resume(self):
        self.say("resuming...")
        domain = self.get_domain(self.name)

        if domain_has_state(domain, libvirt.VIR_DOMAIN_RUNNING):
            self.add("is already running")
            return

        if not domain_has_state(domain, libvirt.VIR_DOMAIN_PAUSED):
            self.add("is not suspended")
            return

        domain.resume()

        if not domain_wait_state(domain, libvirt.VIR_DOMAIN_RUNNING):
            self.warn("could not resumed")
            return

        self.success("resumed!")

    def _spawn_domain(self):
        self.say("spawning...")
        self.xml_dfn = {'devices': ''}

        self.childs_run("spawn")

        # Close open guest connection for this domain
        self.conn().close_guest(self.ident())

        caps = self.get_capabilities()

        xml = paths.template('node.xml')
        self.xml_dfn['name'] = self.name
        self.xml_dfn.update(caps)

        try:
            self.virt().defineXML(xml.safe_substitute(self.xml_dfn))
            domain = self.get_domain(self.name)
            return domain
        except libvirt.libvirtError as err:
            raise error.ExecError(err, "Could not start "
                                          "domain {}".format(self.name))

    def _stop_domain(self, domain, force=False):
        if not domain.isActive():
            self.say("is already stopped")
            return

        if domain_has_state(domain, libvirt.VIR_DOMAIN_PAUSED):
            domain.resume()

        domain.shutdown()

        if not wait_until_inactive(domain):
            if not force:
                self.warn("could not be stopped")
                self.warn("If you want to force shutdown. Try --force")
                return

            # Try to force off
            domain.destroy()
            if not wait_until_inactive(domain):
                self.warn("could not be stopped")
                return
        self.success("stopped!")


NodeComponent.register()
