'''Graphics and rendering management'''

# __pragma__('skip')
from stubs import document, Image, console, __new__
# __pragma__('noskip')

class Graphics:
    canvas = None
    context = None
    width = 160
    height = 144
    clear = True
    smooth = False

    def init():
        console.log( '[graphics] init' )
        Graphics.canvas = document.getElementById( 'canvas' )

    @classmethod
    def setup_context( cls ):
        cls.context = cls.canvas.getContext( '2d' )
        if not cls.smooth:
            cls.disable_smooth()
        # TODO: Respetar relación de aspecto( necesario para fullscreen)
        cls.context.setTransform( cls.canvas.width / cls.width, 0, 0, cls.canvas.height / cls.height, 0, 0 )
        if cls.clear:
            cls.context.clearRect( 0, 0, cls.width, cls.height )

    @classmethod
    def render( cls ):
        # TODO
        pass

    @classmethod
    def disable_smooth( cls ):
        cls.context.mozImageSmoothingEnabled = False
        cls.context.webkitImageSmoothingEnabled = False
        cls.context.msImageSmoothingEnabled = False
        cls.context.imageSmoothingEnabled = False
