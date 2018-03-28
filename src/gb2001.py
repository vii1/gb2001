'''GB 2001 A GameBoy Emulator Odyssey'''

# __pragma__('skip')
from stubs import document, console, __new__, FileReader, Uint8Array
# __pragma__('noskip')

from cart import Cart

def on_openCart_click(e):
    fileInput = document.getElementById('fileInput')
    if fileInput:
        fileInput.click()    

def init_dom():
    openCart = document.getElementById('openCart')
    openCart.addEventListener('click', on_openCart_click, False)

def main():
    init_dom()

def on_FileReader_load(e):
    arrayBuffer = e.target.result
    file = e.target.file['name']
    rom = __new__(Uint8Array(arrayBuffer, 0, arrayBuffer.length))
    c = Cart(file, rom)

def load_cart( file ):
    fr = __new__(FileReader())
    fr.onload = on_FileReader_load
    fr.file = file
    fr.readAsArrayBuffer( file )
