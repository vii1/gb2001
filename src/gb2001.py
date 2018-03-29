'''GB 2001 A GameBoy Emulator Odyssey'''

# __pragma__('skip')
from stubs import document, console, __new__, FileReader, Uint8Array
# __pragma__('noskip')

from cart import Cart
from system import System

def on_fileInput_change(e):
    load_cart(e.target.files[0])

def init_dom():
    fileInput = document.getElementById('fileInput')
    fileInput.addEventListener('change', on_fileInput_change, False)
    openCart = document.getElementById('openCart')
    openCart.addEventListener('click', lambda e: fileInput.click(), False)

def main():
    init_dom()

def on_FileReader_load(e):
    arrayBuffer = e.target.result
    file = e.target.file['name']
    rom = __new__(Uint8Array(arrayBuffer, 0, arrayBuffer.length))
    c = Cart(file, rom)
    document.getElementById('cartName').innerText = file
    s = System(c)

def load_cart( file ):
    fr = __new__(FileReader())
    fr.onload = on_FileReader_load
    fr.file = file
    fr.readAsArrayBuffer( file )
