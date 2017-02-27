from xii.entity import Entity
from xii.store import HasStore
from xii import error


class Component(Entity, HasStore):
    ctype = ""
    """
    Name of the component (eg. 'node')
    """

    default_attributes = []
    """
    List of default attributes which are created if not defined in a
    definition file
    """

    required_attributes = []
    """
    Required attributes for this component
    """

    short_description = None

    def __init__(self, name, command, tpls={}):
        Entity.__init__(self, name, parent=command, templates=tpls)

    def get_virt_url(self):
        return self.get("settings/connection", "qemu://system")

    # limit access to component/type/concret_instance
    def store(self):
        """get the store

        Returns:
            The store with lens to this components settings
        """
        path = "components/{}/{}".format(self.ctype, self.entity())
        return self.parent().store().derive(path)

    def command(self):
        """get owning command

        Returns:
            The command which this component is associated with
        """
        return self.parent()

    def attributes(self):
        """get all attributes

        Returns:
            A list of all already added attributes
        """
        return self._childs

    def add_attribute(self, attribute):
        """add a new attribute

        Args:
            attribute: Attribute object to add
        """
        return self.add_child(attribute)

    def each_attribute(self, action, args=None, reverse=False):
        """run a action on each attribute

        ::
            self.each_attribute("start")
            # reverse order
            self.each_attribute("stop", reverse=True)

        Args:
            action: Action which should be executed
            reverse: Run the action in reversed order
        """
        return self.each_child(action, args, reverse)

    def get_attribute(self, name):
        """get added attribute

        Returns:
            Attribute object or None if not found
        """
        return self.get_child(name)

    def has_attribute(self, name):
        """check if component has attribute

        Returns:
            True if found or False
        """
        return not self.get_child(name) is None

    def get_temp_path(self, *args):
        """get the template path for this component

        All arguments are joined to one path

        Returns:
            Path to the template directory or file
        """
        return self.command().get_temp_path(self.entity(), *args)

    def run(self, action):
        if action in dir(self):
            getattr(self, action)()

    def validate(self):
        Entity.validate(self, self.required_attributes)


def from_definition(definition, command, ext_mgr):
    for component_type in definition:
        for name in definition[component_type].keys():
            cmpnt = ext_mgr.get_component(component_type)

            if not cmpnt:
                raise error.NotFound("Could not find component type {}!"
                                     .format(component_type))
            instance = cmpnt["class"](name, command, cmpnt["templates"])
            _initialize_attributes(instance, ext_mgr)

            yield instance


def _initialize_attributes(instance, ext_mgr):
    non_attributes = ["count", "type", "settings", "basename"]

    def add_attr(name):
        attr = ext_mgr.get_attribute(instance.ctype, name)

        if not attr:
            raise error.NotFound("Invalid attribute `{}` for component "
                                 "{}. Maybe Missspelled?"
                                 .format(name, instance.entity()))

        instance.add_attribute(attr["class"](instance, attr["templates"]))

    # load defined attributes
    for n in instance.store().values().keys():
        if n not in non_attributes:
            add_attr(n)

    # add defaults
    for name in instance.default_attributes:
        if not instance.has_attribute(name):
            add_attr(name)

    # check if all required attributes are set
    for name in instance.required_attributes:
        if not instance.has_attribute(name):
            raise error.NotFound("{} needs a {} attribute but not found, "
                                 "add one!".format(instance.ctype, name))
