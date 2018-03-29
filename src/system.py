from cart import Cart
from memory import Memory
from cpu import Cpu

class System:
    def __init__(self, cart: Cart):
        self.cart = cart
        self.memory = Memory(cart)