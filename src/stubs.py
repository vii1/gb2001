'''Transcrypt compatibility stubs'''

# __pragma__('skip')

window = None
console = None
document = None
FileReader = None

class Audio:
    loop: bool
    src: str
    volume: float

def __new__(newobj):
    return newobj

class Image:
    src: str

class Uint8Array:
    def __init__(self, *args):
        pass
    def __getitem__(self, item):
        pass
    def __setitem__(self, key, value):
        pass
    @property
    def length(self) -> int:
        pass

def Array(*args):
    pass
