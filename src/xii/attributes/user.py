import crypt
import random
import string
import os

from xii import attribute, paths, error
from xii.output import info, show_setting


class UserAttribute(attribute.Attribute):
    name = "user"
    allowed_components = "node"
    defaults = None

    default_user = {"username": "xii",
                    "description": "xii generated user",
                    "shell": "/bin/bash",
                    "password": "xii",
                    "skel": True,
                    "n": 0}

    def __init__(self, value, cmpnt):
        attribute.Attribute.__init__(self, value, cmpnt)

        if (not isinstance(self.value, dict) and self.value is not defaults):
            raise error.InvalidSetting("attribute", "user need to be a dictonary")

    def info(self):
        if self.value:
            show_setting("user", ", ".join(self.value.keys()))

    def get_default_user(self):
        if not self.value:
            return "xii"
        return self.value.iterkeys().next()

    def spawn(self, domain_name):
        if not self.value:
            return

        info("Adding user to domain")
        guest = self.conn().guest(self.cmpnt.attribute('image').clone(domain_name))
        shadow = guest.cat("/etc/shadow").split("\n")
        passwd = guest.cat("/etc/passwd").split("\n")
        groups = guest.cat("/etc/group").split("\n")

        user_index = 0
        for name, settings in self.value.items():
            info("Adding {}".format(name), 2)
            user = self.default_user.copy()
            user['username'] = name
            user['n'] = user_index
            user.update(settings)

            gid, groups = self._add_user_to_groups(groups, user)
            user['gid'] = gid

            uid, passwd = self._add_user_to_passwd(passwd, user)
            user['uid'] = uid

            shadow = self._add_user_to_shadow(shadow, user)

            self._mk_home(guest, user)

            user_index += 1

        guest.write("/etc/shadow", "\n".join(shadow))
        guest.write("/etc/passwd", "\n".join(passwd))
        guest.write("/etc/group", "\n".join(groups))

    def _add_user_to_shadow(self, shadow, user):
        new = self._gen_shadow(user['username'], user['password'])
        for i, line in enumerate(shadow):
            if line.startswith(user['username'] + ":"):
                shadow[i] = new
                return shadow
        shadow.append(new)
        return shadow

    def _add_user_to_passwd(self, passwd, user):
        # Assumption: Every system already has a root user
        if user['username'] == "root":
            return 0, passwd

        uid = 1100 + user['n']

        if 'uid' in user:
            uid = user['uid']

        new = self._gen_passwd(uid, user)
        for i, line in enumerate(passwd):
            if line.startswith(user['username'] + ":"):
                passwd[i] = new
                return uid, passwd
        passwd.append(new)
        return uid, passwd

    def _add_user_to_groups(self, groups, user):

        # Since root group is defined in lsb it must be there
        if user['username'] == 'root':
            return 0, groups

        search = user['username']
        name = user['username']
        gid = 1100 + user['n']

        # if group is set use this
        if 'group' in user:
            search = user['group']
            name = user['group']

        # prefer gid over group name
        if 'gid' in user:
            search = str(user['gid'])
            gid = user['gid']

        for i, line in enumerate(groups):
            if ":" + search + ":" in line:
                if line[-1] != ":":
                    groups[i] += ","
                groups[i] += user['username']
                return gid, groups

        new = ":".join([name, "x", str(gid), user['username']])
        groups.append(new)

        return gid, groups

    def _gen_passwd(self, uid, user):
        home = self._user_home(user)
        elems = [user['username'],
                 "x",  # password is stored in /etc/shadow
                 str(uid),
                 str(user['gid']),
                 user['description'],
                 home,
                 user['shell']]
        return ":".join(elems)

    def _mk_home(self, guest, user):
        home = self._user_home(user)

        if guest.is_dir(home):
            return

        if user['skel']:
            guest.cp_r('/etc/skel', home)
        else:
            guest.mkdir(home)

        paths = [os.path.join(home, path) for path in guest.ls(home)]
        paths.append(home)

        for path in paths:
            guest.chown(user['uid'], user['gid'], path)

    def _user_home(self, user):
        if 'home' in user:
            return user['home']
        return os.path.join('/home', user['username'])

    def _gen_shadow(self, user, password):
        salt = self._generate_salt()
        hashed = crypt.crypt(password, "$6$" + salt + "$")
        return ":".join([user, hashed, "1", "", "99999", "", "", "", ""])

    def _generate_salt(self, length=16):
        chars = string.ascii_letters + string.digits
        return ''.join([random.choice(chars) for _ in range(length)])


attribute.Register.register("user", UserAttribute)