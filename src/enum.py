"""
Very simple Enum implementation because the one included in Python3 is not compatible with Transcrypt.
"""

class EnumItem:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return self.name

    def __repr__(self):
        return "enum(%s: %d)" % (self.name, self.value)

    def __int__(self):
        return self.value

    def __eq__(self, other):
        if type(other) is EnumItem:
            return other.value == self.value
        elif type(other) is str:
            return other == self.name
        else:
            return int(other) == self.value

    def __hash__(self):
        return hash(self.value) ^ hash(self.name)

class EnumMeta(type):
    def __new__(cls, clsname: str, bases: tuple, dct: dict):
        newdct = {}
        fwd = {}
        rev = {}
        for k,v in dict(dct).items():
            if type(v) is int and k[0] != '_':
                item = EnumItem(k, v)
                newdct[k] = item
                fwd[k] = item
                rev[v] = item
            else:
                newdct[k] = v
        newdct['enum_items'] = lambda: fwd.values()
        newdct['enum_names'] = lambda: map(lambda i: i.name, fwd.values())
        newdct['enum_values'] = lambda: map(lambda i: i.value, fwd.values())
        newdct['with_name'] = lambda name: fwd.get(name)
        newdct['with_value'] = lambda value: rev.get(value)
        return type.__new__(cls, clsname, bases, newdct)

class Enum(metaclass=EnumMeta):
    __metaclass__ = EnumMeta
    def __new__(cls, *args, **kwargs):
        value = args[0]
        t = type(value)
        if t is EnumItem:
            return value
        elif t is str:
            return cls.with_name(value)
        else:
            return cls.with_value(int(value))

    @staticmethod
    def enum_items():
        pass
    @staticmethod
    def enum_names():
        pass
    @staticmethod
    def enum_values():
        pass
    @staticmethod
    def with_name(name):
        pass
    @staticmethod
    def with_value(value):
        pass
