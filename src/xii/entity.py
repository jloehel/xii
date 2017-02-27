import string
from xii import error, util
from xii.output import HasOutput

class Entity(HasOutput):
    requires = []
    """
    Each entity can require some other entities in same level.

    For example a attribute can require that there is a another attribute
    which is handled first.
    """

    def __init__(self, name,store=None, parent=None, templates={}):
        self._entity = name
        self._parent = parent
        self._store = store
        self._childs = []
        self._shares = {}
        self._templates = templates

    def has_parent(self):
        """ check if entity has a parent

        Returns:
            True or False
        """
        return self._parent is not None

    def parent(self):
        """get parent

        This method should never called on a parent object.

        Returns:
            The parent objecta

        Throws:
            error.Bug is throw if a parent object trys to access it's parent
        """
        if not self.has_parent():
            raise error.Bug("{} is trying to get parent entity, but there "
                            "is none".format(self.entity()))
        return self._parent

    def entity_path(self):
        """get the complete entity path

        The entity path show the hierachy in which the object is used.

        Example:
        ::

            self.entity_path()
            ["start", "node", "image"]

        Returns:
            The path as list
        """
        if self.has_parent():
            return self._parent.entity_path() + [self._entity]
        return [self._entity]

    def entity(self):
        """ get the entity
        Each entity has a name. eg. NodeObjects entity is 'node'

        Returns:
            The entities name
        """
        return self._entity

    def store(self):
        """ get the store

        Returns:
            The associated store
        """
        return self._store

    # FIXME: Find better place
    def has_component(self, ctype, cmpnt):
        components = self.get("components")

        if not components:
            return False

        if (ctype not in components or
            cmpnt not in components[ctype][cmpnt]):
            return False
        return True

    def config(self, key, default=None):
        """ get global config

        Example:
        ::

            self.config("global/connection")
            "qemu://system"

            self.config("non-existend/key", ["foo", "bar")
            ["foo", "bar"]

        Args:
            key: Key path for configuration
            default: Default value if key path was not found

        Returns:
            The configuration or `default` or None if not `default` set
        """
        if self.has_parent():
            return self.parent().config(key, default)
        return self.store().get(key, default)

    def is_verbose(self):
        return self.config("global/verbose", False) or self.config("command/args/verbose", False)

    def is_parallel(self):
        return self.config("global/parallel", True)

    def template(self, key):
        """get template
        Get a template which was added to the filesystem in the corresponding
        'templates/' directory.

        Example:
        ::

            # path: components/node/attributes/image/templates/disk.xml
            # in image attribute
            self.template("disk.xml")
            < Template('...') >

            # path: components/node/templates/qemu/simple.xml
            # in node component
            self.template("qemu/simple.xml")
            < Template('...') >

        Args:
            key: Key path to template

        Returns:
            The specified template

        Throws:
            error.Bug if template could not found
        """
        if key not in self._templates:
            raise error.Bug("Could not find template {}".format(key))

        content = util.file_read(self._templates[key])
        return string.Template(content)

    def validate(self, required_children=None):
        self.reorder_childs()
        if required_children:
            for required in required_children:
                child = self.get_child(required)
                if not child:
                    raise error.NotFound("Could not find required `{}` "
                                        "in {}".format(required, self.entity()))
        for child in self._childs:
            child.validate()

    def share(self, name, creator, finalizer=None):
        """share a object
        Share a object between this entity and all childs

        Example:

        .. code-block:: python
           :linenos:

            def custom_ssh_to_host():
                def _create_ssh():
                    ssh = Ssh(self, "xii-project.org", "example", password="foo")
                    return ssh

                def _close_ssh(ssh):
                    ssh.close()

                return self.share("uniq_ssh_name", _create_ssh, _close_ssh)

        Args:
            name: A uniq name for this share
            creator: A creator method which returns a shared object
            finalizer: Optional finalizer method which takes the shared object

        Returns:
            A already existing shared object or a newly created
        """
        if name not in self._shares:
            self._shares[name] = {
                "value": creator(),
                "finalizer": finalizer
            }
        return self._shares[name]['value']

    def finalize(self):
        """run finalizer on all shared object

        Remove all shared objects and run finalizer if specified
        """
        for child in self._childs:
            child.finalize()
        for name, shared in self._shares.items():
            if shared["finalizer"] is not None:
                shared["finalizer"](shared['value'])
            del self._shares[name]

    def run(self, action):
        if action in dir(self):
            return getattr(self, action)()

    def add_child(self, new):
        for idx, child in enumerate(self._childs):
            if child.entity() == new.entity():
                self._childs[idx] = new
                return
        self._childs.append(new)

    def get_child(self, entity):
        for child in self._childs:
            if child.entity() == entity:
                return child
        return None

    def get_component(self, name):
        if self.has_parent():
            return self.parent().get_component(name)
        return self.get_child(name)

    def children(self):
        return self._childs

    def each_child(self, action, args=None, reverse=False):
        result = []
        if reverse:
            run = reversed(self._childs)
        else:
            run = self._childs

        for child in run:
            if args is None:
                result.append(child.run(action))
            else:
                import pdb; pdb.set_trace()
                result.append(child.run(action, **args))
        return result

    def child_index(self, entity):
        for idx, child in enumerate(self._childs):
            if child.entity() == entity:
                return idx
        return None

    def reorder_childs(self):
        idx = 0
        rounds = 0
        size = len(self._childs)

        while idx != size:
            has_moved = False
            if rounds > size * 2:
                raise error.Bug("Cyclic dependencies.")

            for requirement in self._childs[idx].requires:
                move = self.child_index(requirement)
                if move is None:
                    continue

                if move > idx:
                    self._childs.insert(idx, self._childs.pop(move))
                    has_moved = True
            if not has_moved:
                idx += 1
            rounds += 1
