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

class EnumMeta(type):
    def __new__(cls, clsname: str, bases: tuple, dct: dict):
        newdct = {}
        items = {}
        for k,v in dict(dct).items():
            if type(v) is int:
                items[k] = v
                newdct[k] = EnumItem(k, v)
            else:
                newdct[k] = v
        newdct['__len__'] = lambda: len(items)
        newdct['items'] = lambda: items.items()
        newdct['keys'] = lambda: items.keys()
        newdct['values'] = lambda: items.values()
        return type.__new__(cls, clsname, bases, newdct)

class Enum:
    __metaclass__ = EnumMeta
