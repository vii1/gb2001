import unittest
from assembler import Assembler

class Test_assembler(unittest.TestCase):
    def test_org(self):
        code = '''
            .org 29
            .byte 100
            .org $29
            .byte $b0
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({29:100,0x29:0xb0}, p)

    def test_byte(self):
        code = '''
            .byte 50
            .byte 10, 666, $99, $fff
            .byte 'hola muy buenas'
            .byte "con el ",34,"rayo de la muerte",34
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0:50,
            1:10,2:154,3:0x99,4:255,
            5: 104, 6: 111, 7: 108, 8: 97, 9: 32, 10: 109, 11: 117, 12: 121, 13: 32, 14: 98, 15: 117, 16: 101, 17: 110, 18: 97, 19: 115,
            20: 99, 21: 111, 22: 110, 23: 32, 24: 101, 25: 108, 26: 32, 27: 34, 28: 114, 29: 97, 30: 121, 31: 111, 32: 32, 33: 100, 34: 101, 35: 32, 36: 108, 37: 97, 38: 32, 39: 109, 40: 117, 41: 101, 42: 114, 43: 116, 44: 101, 45: 34
        }, p)

    def test_word(self):
        code = '''
            .word $cafebabe
            .word $cafe, $babe
            .word 1, 2, 3
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0: 0xbe, 1: 0xba,
            2: 0xfe, 3: 0xca, 4: 0xbe, 5: 0xba,
            6: 1, 7: 0, 8: 2, 9: 0, 10: 3, 11: 0
        }, p)

    def test_align(self):
        code = '''
            .org 0
            .byte 'A'
            .align 8
            .byte 'B'
            .align $100
            .align 4
            .byte 'C'
            .align 4
            .byte 'D'
            .align $100
            .byte 'E'
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0: 65, 8: 66, 0x100: 67, 0x104: 68, 0x200: 69
        }, p)

    def test_equ(self):
        code = '''
            .equ prueba1 $100
            .equ valorbyte 34
            .equ prueba2 valorbyte
            .org prueba1
            .byte valorbyte
            .word prueba2
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0x100: 34, 0x101: 34, 0x102: 0
        }, p)

    def test_labels(self):
        code = '''
            .byte $11
            .word HOLA
            .org $99F
            HOLA: .word BUENAS
            BUENAS .word HOLA
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0: 0x11, 1: 0x9F, 2: 0x09,
            0x99F: 0xA1, 0x9A0: 0x09,
            0x9A1: 0x9F, 0x9A2: 0x09
        }, p)

    def sub_test_ALU(self, name, opcode):
        code = f'''
            {name} A,B
            {name} D
            {name} (HL)
            {name} A, (HL)
            {name} A, A
            {name} A
            {name} L
            {name} A, 9
            {name} $90
            {name} lab
            {name} A, lab
            lab:
        '''
        p = Assembler(code).get_patch()
        self.assertEqual({
            0: opcode | 0x80,
            1: opcode | 0x82,
            2: opcode | 0x86,
            3: opcode | 0x86,
            4: opcode | 0x87,
            5: opcode | 0x87,
            6: opcode | 0x85,
            7: opcode | 0xC6, 8: 9,
            9: opcode | 0xC6, 10: 0x90,
            11: opcode | 0xC6, 12: 15,
            13: opcode | 0xC6, 14: 15,
            }, p)

    def test_ADC(self):
        self.sub_test_ALU('ADC', 0x08)

    def test_ADD(self):
        self.sub_test_ALU('ADD', 0)

    def test_AND(self):
        self.sub_test_ALU('AND', 0x20)

    def test_CP(self):
        self.sub_test_ALU('CP', 0x38)

    def test_OR(self):
        self.sub_test_ALU('OR', 0x30)

    def test_SBC(self):
        self.sub_test_ALU('SBC', 0x18)

    def test_SUB(self):
        self.sub_test_ALU('SUB', 0x10)

    def test_XOR(self):
        self.sub_test_ALU('XOR', 0x28)


if __name__ == '__main__':
    unittest.main()
