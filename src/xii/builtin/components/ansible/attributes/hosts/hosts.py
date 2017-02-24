import os

from xii.components.ansible import AnsibleAttribute
from xii.validator import List, String, Dict, VariableKeys, Or
from xii.need import NeedLibvirt, NeedIO, NeedSSH
from xii import util


class HostsAttribute(AnsibleAttribute, NeedLibvirt, NeedIO, NeedSSH):
    atype = "hosts"
    defaults = None
    keys = Or([
        String("wildcard*"),
        List(String("hosts")),
        Dict([VariableKeys(List(String("hosts")), example="hostname")])
    ])

    def _fetch_ips(self, hosts):
        def _to_tuple(host):
            return (host, self.domain_get_ip(host, quiet=True))
        return util.in_parallel(3, hosts, _to_tuple)

    def _check_ssh_servers(self, hosts):
        def _check_ssh(host, ip):
            if self.ssh_host_alive(ip):
                return (host, ip)
            return None
        return filter(None, util.in_parallel(3, hosts, lambda x: _check_ssh(*x)))

    def generate_inventory(self, tmp):
        known_hosts = {}
        hosts       = self._get_hosts()
        inventory   = os.path.join(tmp,"inventory")
        to_write    = []
        all_hosts   = []

        # fetch all hostnames
        map(all_hosts.extend, self._get_hosts().values())
        all_hosts = list(set(all_hosts))

        # fetch ips and check ssh connectifity
        ips = self._fetch_ips(all_hosts)
        ips = self._check_ssh_servers(ips)

        for group, hosts in self._get_hosts().items():
            to_write.append("[{}]".format(group))

            for host in hosts:
                ip = self.domain_get_ip(host, quiet=self.is_verbose())

                cmpnt = self.get_component(host)

                if ip is None:
                    raise error.ExecError("Could not fetch all required ip "
                                        "addresses")
                entry = [
                    host,
                    "ansible_connection=ssh",
                    "ansible_port=22",
                    "ansible_host={}".format(ip),
                    "ansible_user={}".format(cmpnt.ssh_user())
                ]
                to_write.append("\t".join(entry))

        with self.io().open(inventory, "w") as inv:
            inv.write("\n".join(to_write))

        return inventory

    def _get_hosts(self):
        # Add python3 compatibility
        try:
            basestring
        except NameError:
            basestring = str

        if isinstance(self.settings(), basestring):
            instances = self.command().get_components(self.settings(), "node")
            names = map(lambda i: i.entity(), instances)
            return { "all": names }

        if isinstance(self.settings(), dict):
            return self.settings()

        # a list is given
        if isinstance(self.settings(), list):
            return {"all": self.settings()}

        raise error.Bug("Can not create host list for ansible")
