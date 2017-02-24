from xii.entity import Entity
from xii.store import HasStore, Store
from xii import error


class Attribute(Entity, HasStore):
    atype = ""
    """
    Set the attributes name
    """

    defaults = None
    """
    Set default settings which are used if the attribute is created
    by default (see _component)
    """

    keys = None
    """
    Defines the configuration validator for this attribute.

    Each attributes can has several settings. To make validation more
    consistent a validator has to be specified. See _validation for more
    information.

    Examples:
    ::

        # just a string
        keys = String()

        # A dict with a required key and optional
        # settings (string and a list of strings
        keys = Dict([
          RequiredKey("key1", String()),
          Key("key2", String()),
          Key("key3", List(String()))
        ])

        # a string `or` a boolean
        keys = Or([String(), Bool()])
    """

    @classmethod
    def has_defaults(cls):
        if cls.defaults is None:
            return False
        return True

    def __init__(self, component, tpls):
        """Initialize the attribute.

        Do not forget to call Attribute.__init__() on a custom constructor

        Args:
            component: the parent component which owns the attribute instance
            tpls: templates assosiated with this attribute
        """
        Entity.__init__(self,
                        name=self.atype,
                        parent=component,
                        templates=tpls)

    def settings(self, key=None, default=None):
        """return validated settings

        This function will return the searched key or all settings if
        not `key` is specified.

        Args:
            key: Search key eg. "settingsdict/key1" or "foo" or None
            default: If key is not found in settings default is returned

        Returns:
            Value specified in `default` or None
        """
        if self.store().has_key(self.atype):
            s = self.store().derive(self.atype)
        elif self.has_defaults():
            s = Store(parent=self.defaults)
        else:
            raise error.Bug("Try to get default settings for {} but "
                            "no defaults are defined".format(self.entity()))
        if key is None:
            return s.values()
        return s.get(key, default)

    def share(self, name, creator, finalizer=None):
        """Add a shared object to the owning component.

        If you want to use a shared object which should not recreated each
        time a attribute calls a specific method or is used in more than one
        attribute (eg. ssh connection) you can use a share.

        Each share needs a uniq name and a creator method which creates the
        object.
        Once one object was create share will return this object until the
        finalizer has run.

        Example:
        .. code-block:: python
            :linenos:

            def custom_ssh_to_host():
                def _create_ssh():
                    ssh = Ssh(self, "example.org", "example", password="foo")
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
        return self.parent().share(name, creator, finalizer)

    def store(self):
        """get the store of the component

        Returns:
            The store of the parent component
        """
        return self.parent().store()

    def component(self):
        """get the owning component

        Returns:
            The owning component
        """
        return self.parent()

    def command(self):
        """get the owning command

        Returns:
            The owning command
        """
        return self.component().command()

    def component_entity(self):
        """get the owing components entity

        Returns:
            The owning components entity as string
        """
        return self.parent().entity()

    def other_attribute(self, name):
        """get another attribute which is also used by the owning component

        Args:
            Name of the attribute to fetch

        Returns:
            Returns the attribute object or None if not found
        """
        return self.parent().get_attribute(name)

    def validate(self):
        """validate the settings of a attribute

        To add custom setting validation overwrite this class method and
        call the parent method

        This method communicates validation errors as fatal exeception with no
        return value.

        Check _`exception handling` for more information on execeptions.
        """
        path = self.component_entity() + " > " + self.entity()
        self.keys.validate(path, self.settings())

    def get_temp_path(self, *args):
        """get the temporay path for this attribute

        All arguments are joined to one path

        Returns:
            Path, with no checks if it's valid
        """
        return self.component().get_temp_path(*args)

    def get_virt_url(self):
        return self.get("settings/connection", "FAILING")
