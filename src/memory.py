# __pragma__('skip')
from stubs import Uint8Array
# __pragma__('noskip')

from cart import Cart, Mbc

class Memory:
    def __init__(self, cart: Cart):
        self.enable_bootrom = True
        self.rom = cart.rom

    def peek(self, addr):
        addr &= 0xFFFF

    def poke(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF