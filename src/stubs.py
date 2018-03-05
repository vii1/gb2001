'''Transcrypt compatibility stubs'''

# __pragma__('skip')

window = None
console = None
document = None

class Audio:
    loop: bool
    src: str
    volume: float

def __new__(newobj):
    return newobj

class Image:
    src: str

# __pragma__('noskip')