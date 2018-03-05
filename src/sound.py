'''Sound and music management'''

# __pragma__('skip')
from stubs import window, console, Audio, __new__
# __pragma__('noskip')

class Sound:
    context = None
    disabled = False

    @classmethod
    def init( cls ):
        console.log( '[sound] init' )
        cls._master_volume = 0.5
        AudioContext = window.AudioContext or window.webkitAudioContext
        if not AudioContext:
            console.log( '[sound] ERROR: No AudioContext API detected. Disabling sound.' )
            cls.disabled = True
            return
        cls.context = __new__( window.AudioContext() )
