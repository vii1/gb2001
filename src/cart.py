'''Cartridge class'''

# __pragma__('skip')
from stubs import console, __new__, Uint8Array
# __pragma__('noskip')

class Cart:
    def __init__(self, file : str, rom : Uint8Array ):
        self.rom = rom
        console.debug(f"Loaded ROM: {file} - {rom.length} bytes")
        logo = __new__(Uint8Array([206, 237, 102, 102, 204, 13, 0, 11, 3, 115, 0, 131, 0, 12, 0, 13, 0, 8, 17, 31, 136, 137, 0, 14, 220, 204, 110, 230, 221, 221, 217, 153, 187, 187, 103, 99, 110, 14, 236, 204, 221, 220, 153, 159, 187, 185, 51, 62]))
        ok = True
        for i in range(len(logo)):
            if rom[0x104+i] != logo[i]:
                ok = False
                break
        console.debug('ROM Logo check ...', 'OK' if ok else 'ERROR !!!')
