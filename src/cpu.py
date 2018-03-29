from memory import Memory

class Cpu:
    @property
    def A(self):
        """A (accumulator) register"""
        return self._a
    @A.setter
    def A(self, value):
        self._a = value & 0xFF

    @property
    def F(self):
        """F (flags) register"""
        return self._f
    @F.setter
    def F(self, value):
        self._f = value & 0xFF

    @property
    def B(self):
        """B auxiliary register"""
        return self._b
    @B.setter
    def B(self, value):
        self._b = value & 0xFF

    @property
    def C(self):
        """C auxiliary register"""
        return self._c
    @C.setter
    def C(self, value):
        self._c = value & 0xFF

    @property
    def D(self):
        """D auxiliary register"""
        return self._d
    @D.setter
    def D(self, value):
        self._d = value & 0xFF

    @property
    def E(self):
        """E auxiliary register"""
        return self._e
    @E.setter
    def E(self, value):
        self._e = value & 0xFF

    @property
    def H(self):
        """H auxiliary register"""
        return self._h
    @H.setter
    def H(self, value):
        self._h = value & 0xFF

    @property
    def L(self):
        """L auxiliary register"""
        return self._l
    @L.setter
    def L(self, value):
        self._l = value & 0xFF

    @property
    def PC(self):
        """PC (Program Counter) register"""
        return self._pc
    @PC.setter
    def PC(self, value):
        self._pc = value & 0xFFFF

    @property
    def SP(self):
        """SP (Stack Pointer) register"""
        return self._sp
    @SP.setter
    def SP(self, value):
        self._sp = value & 0xFFFF

    @property
    def AF(self):
        """AF pair register"""
        return (self._a << 8) | self._f
    @AF.setter
    def AF(self, value):
        self._f = value & 0xFF
        self._a = (value >> 8) & 0xFF

    @property
    def BC(self):
        """BC pair register"""
        return (self._b << 8) | self._c
    @BC.setter
    def BC(self, value):
        self._c = value & 0xFF
        self._b = (value >> 8) & 0xFF

    @property
    def DE(self):
        """DE pair register"""
        return (self._d << 8) | self._e
    @DE.setter
    def DE(self, value):
        self._e = value & 0xFF
        self._d = (value >> 8) & 0xFF

    @property
    def HL(self):
        """HL pair register"""
        return (self._h << 8) | self._l
    @HL.setter
    def HL(self, value):
        self._l = value & 0xFF
        self._h = (value >> 8) & 0xFF

    @property
    def Z(self):
        """Zero flag (bit 7 of F)"""
        return bool(self.F & 0x80)
    @Z.setter
    def Z(self, value):
        if value:
            self.F |= 0x80
        else:
            self.F &= ~0x80

    @property
    def N(self):
        """Substraction flag (bit 6 of F)"""
        return bool(self.F & 0x40)
    @N.setter
    def N(self, value):
        if value:
            self.F |= 0x40
        else:
            self.F &= ~0x40

    @property
    def HC(self):
        """Half-Carry flag (bit 5 of F)"""
        return bool(self.F & 0x20)
    @HC.setter
    def HC(self, value):
        if value:
            self.F |= 0x20
        else:
            self.F &= ~0x20

    @property
    def CY(self):
        """Carry flag (bit 4 of F)"""
        return bool(self.F & 0x10)
    @CY.setter
    def CY(self, value):
        if value:
            self.F |= 0x10
        else:
            self.F &= ~0x10

    def __init__(self, memory: Memory):
        self.memory = memory
        self._a = 0
        self._f = 0
        self._b = 0
        self._c = 0
        self._d = 0
        self._e = 0
        self._h = 0
        self._l = 0
        self._pc = 0
        self._sp = 0
