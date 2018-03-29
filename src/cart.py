'''Cartridge class'''

# __pragma__('skip')
from stubs import console, __new__, Uint8Array, String
# __pragma__('noskip')

from .enum import Enum

class Capability(Enum):
    Capable = 0
    Required = 1
    Unavailable = 2

class Mbc(Enum):
    Nil = 0
    MBC1 = 1
    MBC2 = 2
    MMM01 = 3
    MBC3 = 4
    MBC4 = 5
    MBC5 = 6
    HuC3 = 7
    HuC1 = 8

class CartType:
    def __init__(self, desc):
        self.description = desc
        self.mbc = Mbc.Nil
        for i in Mbc.enum_items():
            if i.name in desc:
                self.mbc = i
                break
        self.ram = 'RAM' in desc
        self.timer = 'TIMER' in desc
        self.battery = 'BATT' in desc
        self.rumble = 'RUMBLE' in desc

cart_types = {
    0x00: CartType('ROM ONLY'),
    0x01: CartType('MBC1'),
    0x02: CartType('MBC1+RAM'),
    0x03: CartType('MBC1+RAM+BATTERY'),
    0x05: CartType('MBC2'),
    0x06: CartType('MBC2+BATTERY'),
    0x08: CartType('ROM+RAM'),
    0x09: CartType('ROM+RAM+BATTERY'),
    0x0B: CartType('MMM01'),
    0x0C: CartType('MMM01+RAM'),
    0x0D: CartType('MMM01+RAM+BATTERY'),
    0x0F: CartType('MBC3+TIMER+BATTERY'),
    0x10: CartType('MBC3+TIMER+RAM+BATTERY'),
    0x11: CartType('MBC3'),
    0x12: CartType('MBC3+RAM'),
    0x13: CartType('MBC3+RAM+BATTERY'),
    0x15: CartType('MBC4'),
    0x16: CartType('MBC4+RAM'),
    0x17: CartType('MBC4+RAM+BATTERY'),
    0x19: CartType('MBC5'),
    0x1A: CartType('MBC5+RAM'),
    0x1B: CartType('MBC5+RAM+BATTERY'),
    0x1C: CartType('MBC5+RUMBLE'),
    0x1D: CartType('MBC5+RUMBLE+RAM'),
    0x1E: CartType('MBC5+RUMBLE+RAM+BATTERY'),
    0xFC: CartType('POCKET CAMERA'),
    0xFD: CartType('BANDAI TAMA5'),
    0xFE: CartType('HuC3'),
    0xFF: CartType('HuC1+RAM+BATTERY'),
}

rom_sizes = {
    0x00: 2,
    0x01: 4,
    0x02: 8,
    0x03: 16,
    0x04: 32,
    0x05: 64,
    0x06: 128,
    0x07: 256,
    0x52: 72,
    0x53: 80,
    0x54: 96,
}

ram_sizes = {
    0x00: 0,
    0x01: 2,
    0x02: 8,
    0x03: 32,
}

class Cart:
    def __init__(self, file, rom: Uint8Array):
        self.rom = rom
        console.debug(f"Loaded ROM: {file} - {rom.length} bytes")
        console.debug('ROM Logo check ...', 'OK' if self.check_logo() else 'ERROR !!!')
        self.cgb_flag = {
            0b10: Capability.Capable,
            0b11: Capability.Required,
        }.get( rom[0x143] >> 6, Capability.Unavailable )
        console.debug(f'CGB Flag ... {self.cgb_flag} -', 'Supported' if self.cgb_flag != Capability.Required else 'NOT SUPPORTED !!!')
        self.sgb_flag = Capability.Capable if rom[0x146] & 3 == 3 else Capability.Unavailable
        console.debug(f'SGB Flag ... {self.sgb_flag}')
        if self.cgb_flag != Capability.Unavailable:
            if all(rom.slice(0x13F, 0x143)):
                title_length = 11
                self.manufacturer = String.fromCharCode.apply(None, rom.slice(0x13F, 0x143))
                console.debug(f'Manufacturer code: {self.manufacturer}')
            else:
                title_length = 15
        else:
            title_length = 16
        self.title = String.fromCharCode.apply(None, rom.slice(0x134, 0x134+title_length))
        cero = self.title.indexOf('\0')
        if cero > -1:
            self.title = self.title[0:cero]
        console.debug(f'Cart title: {self.title}')
        self.cart_type_id = rom[0x147]
        self.cart_type = cart_types[self.cart_type_id]
        console.debug('Cart type: ' + self.cart_type.description)
        self.rom_size_id = rom[0x148]
        self.rom_size = rom_sizes[self.rom_size_id]
        console.debug(f'ROM size: {self.rom_size * 16} KB')
        self.ram_size_id = rom[0x149]
        self.ram_size = ram_sizes[self.ram_size_id]
        console.debug(f'RAM size: {self.ram_size} KB')
        self.destination_id = rom[0x14A]
        console.debug(f"Destination: {'Non-Japanese' if self.destination_id else 'Japanese'}")
        console.debug('Header checksum ...', 'OK' if self.check_header_checksum() else 'ERROR !!!')
        console.debug('Full ROM checksum ...', 'OK' if self.check_rom_checksum() else 'ERROR !!!')

    def check_logo(self):
        logo = __new__(Uint8Array([206, 237, 102, 102, 204, 13, 0, 11, 3, 115, 0, 131, 0, 12, 0, 13, 0, 8, 17, 31, 136, 137, 0, 14, 220, 204, 110, 230, 221, 221, 217, 153, 187, 187, 103, 99, 110, 14, 236, 204, 221, 220, 153, 159, 187, 185, 51, 62]))
        for i in range(len(logo)):
            if self.rom[0x104+i] != logo[i]:
                return False
        return True

    def check_header_checksum(self):
        sum = 0x19
        for i in range(0x134, 0x14E):
            sum += self.rom[i]
        return (sum & 0xFF) == 0 #self.rom[0x14D]

    def check_rom_checksum(self):
        sum = 0
        for i in range(0, 0x14E):
            sum = (sum + self.rom[i]) & 0xFFFF
        for i in range(0x150, len(self.rom)):
            sum = (sum + self.rom[i]) & 0xFFFF
        return (sum >> 8) & 0xFF == self.rom[0x14E] and (sum & 0xFF) == self.rom[0x14F]