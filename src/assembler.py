"""
Assembler
"""

class AssemblerError( Exception ):
    def __init__(self, line, col, msg):
        super().__init__(line, col, msg)
        self.line = line
        self.col = col
        self.msg = msg

    def __str__(self):
        return f"Assembler error: line {self.line}, col {self.col}: {self.msg}"

def _getwhile(cadena, pos, fn):
    tok = ''
    while pos < len(cadena) and fn(cadena[pos]):
        tok += cadena[pos]
        pos += 1
    return (tok, pos)

class Assembler:
    _directives = {'ORG','BYTE','WORD','ALIGN','EQU'}
    _keywords = {'ADC','ADD','AND','BIT','CALL','CCF','CP','CPL','DAA','DEC','DI','EI','HALT','INC','JP','JR',
        'LD','LDD','LDH','LDI','NOP','OR','POP','PUSH','RES','RET','RETI','RL','RLA','RLC','RLCA','RR','RRA',
        'RRC','RRCA','RST','SBC','SCF','SET','SLA','SRA','SRL','STOP','SUB','SWAP','XOR'}
    _r8 = {'A','B','C','D','E','H','L'}
    _r16 = {'AF','BC','DE','HL','SP'}
    _cc = {'Z','NZ','C','NC'}
    _special = {'HLD', 'HLI'}
    _vec = {0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38}

    _destination = {
        'B':    0b000,
        'C':    0b001,
        'D':    0b010,
        'E':    0b011,
        'H':    0b100,
        'L':    0b101,
        '(HL)': 0b110,
        'A':    0b111,
    }

    _cc_code = {
        'NZ': 0b00,
        'Z':  0b01,
        'NC': 0b10,
        'C':  0b11,
    }

    _r16_1 = {
        'BC': 0,
        'DE': 1,
    }

    _r16_2 = {
        'BC': 0b00,
        'DE': 0b01,
        'HL': 0b10,
        'SP': 0b11,
    }

    _r16_3 = {
        'BC': 0b00,
        'DE': 0b01,
        'HL': 0b10,
        'AF': 0b11,
    }

    def __init__(self, code=None):
        if code:
            self.compile(code)

    def compile(self, code):
        self.code = code
        # _mem es hash en vez de array porque puede contener espacios vacíos
        self._mem = {}
        self._imem = 0
        # Relaciona label->imem.
        self._labels = {}
        # Relaciona imem->label para las aún no resueltas.
        self._gaps8 = {}
        self._gaps16 = {}
        self._gapsrel8 = {}
        self._line = 0
        self._col = 0
        self._parse()

    def get_patch(self):
        return self._mem

    def patch(self, memarray):
        for addr,value in self._mem.items():
            memarray[addr] = value
            
    def _error(self, msg):
        raise AssemblerError(self._line, self._col, msg)

    def _warning(self, msg):
        print(f"Assembler warning: line {self._line}, col {self._col}: {msg}")

    def _set_byte(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        self._mem[addr] = value

    def _out_byte(self, value):
        self._set_byte(self._imem, value)
        self._imem = (self._imem + 1) & 0xFFFF

    def _set_word(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFFFF
        # Z80 es little endian
        self._mem[addr] = value & 0xFF
        self._mem[(addr+1) & 0xFFFF] = (value & 0xFF00) >> 8

    def _out_word(self, value):
        self._set_word(self._imem, value)
        self._imem = (self._imem + 2) & 0xFFFF

    def _token(self):
        if self._tok is None:
            self._next_token()
        return self._tok

    def _set_token(self, tok):
        self._tok = tok
        return tok

    def _gen_tokenizer(self):
        for line in self.code.splitlines():
            line = line.rstrip()
            self._line += 1
            self._col = 0
            while self._col < len(line):
                ch = line[self._col]
                if ch.isspace():
                    self._col = _getwhile(line, self._col + 1, str.isspace)[1]
                elif ch == ';':
                    break
                elif ch.isalpha() or ch == '@' or ch == '_' or ch == '.':
                    tok, self._col = _getwhile(line, self._col + 1, lambda c: c.isalnum() or c=='_' or c=='@')
                    yield self._set_token( (ch + tok).upper() )
                elif ch == '$':
                    tok, self._col = _getwhile(line, self._col + 1, lambda c: '0' <= c <= '9' or 'A' <= c.upper() <= 'F')
                    yield self._set_token( int(tok, 16) )
                elif ch == '%':
                    tok, self._col = _getwhile(line, self._col + 1, lambda c: c=='0' or c=='1')
                    yield self._set_token( int(tok,2) )
                elif ch == '0':
                    tok, self._col = _getwhile(line, self._col + 1, lambda c: '0' <= c <= '7')
                    yield self._set_token( int('0'+tok,8) )
                elif ch.isdecimal():
                    tok, self._col = _getwhile(line, self._col + 1, str.isdecimal)
                    yield self._set_token( int(ch+tok) )
                elif ch == '"' or ch == "'":
                    tok, self._col = _getwhile(line, self._col + 1, lambda c: c != ch)
                    if self._col >= len(line) or line[self._col] != ch:
                        self._error('Unclosed string literal')
                    self._col += 1
                    yield self._set_token( '"' + tok )
                elif ch in ',():+-*<>':
                    self._col += 1
                    yield self._set_token( ch )
                else:
                    self._error(f"Invalid character: '{ch}'")

    def _next_token(self):
        try:
            self._tok = next(self._tokenizer)
        except StopIteration:
            self._tok = None
        return self._tok

    def _parse(self):
        self._pos = 0
        self._tok = None
        self._tokenizer = self._gen_tokenizer()
        while self._token() is not None:
            tok = self._token()
            if tok[0] == '.':
                self._parse_directive(tok)
            elif tok in self._keywords:
                self._parse_instruction(tok)
            elif self._is_valid_label(tok):
                self._parse_label(tok)
            else:
                self._error(f"Unexpected token: '{tok}'")
        if self._gaps8 or self._gaps16:
            labels = set(self._gaps8.values()) | set(self._gaps16.values())
            self._error(f"Unresolved labels: {labels}")

    def _parse_directive(self, tok):
        if tok[0] == '.':
            tok = tok[1:]
        fn = {
            'ORG': self._parse_d_org,
            'BYTE': self._parse_d_byte,
            'WORD': self._parse_d_word,
            'ALIGN': self._parse_d_align,
            'EQU': self._parse_d_equ,
        }.get(tok, None)
        if not fn:
            self._error( f'Invalid directive: {tok}' )
        fn( self._next_token() )

    def _parse_d_org(self, tok):
        addr = self._parse_int(tok)
        addr &= 0xFFFF
        self._imem = addr
        self._next_token()

    def _parse_d_byte(self, tok):
        if type(tok) is str and len(tok) > 0 and tok[0] == '"':
            for c in tok[1:]:
                self._out_byte(c.encode('latin-1','ignore')[0])
        else:
            self._out_byte(self._parse_int8(tok))
        if self._next_token() == ',':
            self._parse_d_byte(self._next_token())

    def _parse_d_word(self, tok):
        self._out_word(self._parse_int16(tok))
        if self._next_token() == ',':
            self._parse_d_word(self._next_token())

    def _parse_d_align(self, tok):
        if type(tok) is not int:
            self._error(f"Expecting integer, found '{tok}'")
        addr = self._imem + tok - (self._imem % tok)
        addr &= 0xFFFF
        self._imem = addr
        self._next_token()

    def _is_valid_label(self, tok):
        if len(tok) == 0: return False
        if not ( tok[0].isalpha() or tok[0]=='@' or tok[0]=='_' ): return False
        if tok in self._keywords or tok in self._r8 or tok in self._r16 or \
            tok in self._cc or tok in self._special:
            return False
        return all(map(lambda c: c.isalnum() or c=='@' or c=='_', tok[1:]))

    def _parse_d_equ(self, tok):
        if type(tok) is not str:
            self._error(f"Expecting id, found '{tok}'")
        if not self._is_valid_label(tok):
            self._error(f"Invalid id: '{tok}'")
        value = self._parse_int(self._next_token())
        self._set_label(tok, value)
        self._next_token()

    def _set_label(self, label, value):
        self._labels[label] = value
        self._fill_gaps(label, value)

    def _parse_int(self, tok, size=None, addr=None):
        if addr is None:
            addr = self._imem
        neg = False
        self._resolved = True
        if type(tok) is str and self._is_valid_label(tok):
            value = self._labels.get(tok, None)
            if value is None:
                self._resolved = False
                if size == 8:
                    self._gaps8[addr] = tok
                elif size == 16:
                    self._gaps16[addr] = tok
                elif size == -8:
                    self._gapsrel8[addr] = tok
                else:
                    self._error(f"Undefined label not allowed: '{tok}'")
                value = 0
            return value
        elif tok == '-':
            neg = True
            tok = self._next_token()
        elif tok == '+':
            tok = self._next_token()
        if type(tok) is not int:
            self._error(f"Expecting int{size or ''} constant, found '{tok}'")
        return -tok if neg else tok

    def _parse_rel_offset(self, tok, addr=None):
        return self._parse_int(tok, -8, addr)

    def _parse_int8(self, tok, addr=None):
        return self._parse_int(tok, 8, addr)

    def _parse_int16(self, tok, addr=None):
        return self._parse_int(tok, 16, addr)

    def _fill_gaps(self, label, value):
        for addr,l in [*self._gaps16.items()]:
            if l == label:
                self._set_word(addr, value)
                self._gaps16.pop(addr)
        for addr,l in [*self._gaps8.items()]:
            if l == label:
                self._set_byte(addr, value)
                self._gaps8.pop(addr)
        for addr,l in [*self._gapsrel8.items()]:
            if l == label:
                offset = value - (addr - 1)
                if offset < -127 or offset > 129:
                    self._error(f"Relative jump too far: from ${hex(addr-1)[2:]} to {label} (${hex(value)[2:]})")
                else:
                    self._set_byte(addr, offset + 2)

    def _parse_instruction(self, tok):
        fn = {
            'ADC': self._parse_ALU,
            'ADD': self._parse_ALU,
            'AND': self._parse_ALU,
            'BIT': self._parse_BIT,
            'CALL': self._parse_CALL_JP,
            'CCF': 0x3F,
            'CP': self._parse_ALU,
            'CPL': 0x2F,
            'DAA': 0x27,
            'DEC': self._parse_INC_DEC,
            'DI': 0xF3,
            'EI': 0xFB,
            'HALT': 0x76,
            'INC': self._parse_INC_DEC,
            'JP': self._parse_CALL_JP,
            'JR': self._parse_JR,
            'LD': self._parse_LD,
            'LDD': self._parse_LDD,
            'LDH': self._parse_LDH,
            'LDI': self._parse_LDI,
            'NOP': 0x00,
            'OR': self._parse_ALU,
            'POP': -1,
            'PUSH': -1,
            'RES': self._parse_BIT,
            'RET': -1,
            'RETI': 0xD9,
            'RL': -1,
            'RLA': -1,
            'RLC': -1,
            'RLCA': -1,
            'RR': -1,
            'RRA': -1,
            'RRC': -1,
            'RRCA': -1,
            'RST': -1,
            'SBC': self._parse_ALU,
            'SCF': 0x37,
            'SET': self._parse_BIT,
            'SLA': -1,
            'SRA': -1,
            'SRL': -1,
            'STOP': 0x10,
            'SUB': self._parse_ALU,
            'SWAP': -1,
            'XOR': self._parse_ALU,
            }.get(tok)
        if fn is int:
            self._out_byte(fn)
        else:
            fn(tok)

    def _parse_label(self, tok):
        if self._next_token() == ':':
            self._next_token()
        self._set_label(tok, self._imem)

    def _expect(self, tok, expected):
        if tok != expected:
            self._error(f"Expecting '{expected}', found '{tok}'")

    def _next_expect(self, expected):
        return self._expect(self._next_token(), expected)

    def _parse_destination(self, tok):
        if tok == '(':
            self._next_expect('HL')
            self._next_expect(')')
            return 6 # self._destination['(HL)']
        elif tok in self._r8:
            return self._destination[tok]
        else:
            self._error(f"Expecting destination, found '{tok}'")

    def _parse_ALU(self, tok):
        code = ['ADD','ADC','SUB','SBC','AND','XOR','OR','CP'].index(tok) << 3
        tok = self._next_token()
        # Indicar A como destino es opcional en este ensamblador
        if tok == 'A':
            if self._next_token() == ',':
                tok = self._next_token()
            else:
                self._out_byte(code | 7 | 0x80)
                return
        if tok in self._r8 or tok == '(':
            dest = self._parse_destination(tok)
            self._out_byte(code | dest | 0x80)
        else:
            self._out_byte(code | 0xc6)
            n = self._parse_int8(tok)
            self._out_byte(n)
        self._next_token()

    def _parse_BIT(self, tok):
        code = [0, 'BIT', 'RES', 'SET'].index(tok) << 6
        n = self._parse_int(self._next_token())
        if n < 0 or n > 7:
            self._error(f"Parameter 1 for {tok} must be in range 0..7")
        dest = self._parse_destination(self._next_token())
        self._out_byte(0xCB)
        self._out_byte(code | (n << 3) | dest)

    def _parse_CALL_JP(self, tok):
        call = tok == 'CALL'
        tok = self._next_token()
        if tok in self._cc:
            self._next_expect(',')
            code = 0xC4 if call else 0xC2
            code |= (self._cc_code[tok] << 3)
            self._out_byte(code)
            tok = self._next_token()
        else:
            self._out_byte(0xCD if call else 0xC3)
        addr = self._parse_int16(tok)
        self._out_word(addr)

    def _parse_INC_DEC(self, tok):
        op = 0 if tok == 'INC' else 1
        tok = self._next_token()
        if tok in self._r16_2.keys():
            code = 0x03 | (op << 3) | (self._r16_2[tok] << 4)
            self._out_byte(code)
        elif tok in self._r8 or tok == '(':
            dest = self._parse_destination(tok)
            code = 0x04 | op | (dest << 3)
            self._out_byte(code)
        else:
            self._error(f"Expected destination, found '{tok}'")

    def _parse_JR(self, tok):
        tok = self._next_token()
        if tok in self._cc:
            code = 0x20 | (self._cc_code[tok] << 3)
            self._next_expect(',')
        else:
            code = 0x18
        self._out_byte(code)
        tok = self._next_token()
        if tok == '*':
            tok = self._next_token()
            if tok == '+' or tok == '-':
                tok = self._parse_int(tok) - 2
                if tok < -127 or tok > 129:
                    self._error(f"Relative jump too far: {tok}")
                else:
                    self._out_byte(tok)
            else:
                self._error(f"Expected relative offset, found '{tok}'")
        else:
            tok = self._parse_rel_offset(tok)
            offset = tok - (self._imem - 1)
            if offset < -127 or offset > 129:
                self._error(f"Relative jump too far: {offset}")
            else:
                self._out_byte(offset + 2)

    def _unexpected(self, tok):
        self._error(f"Unexpected token: '{tok}'")

    def _parse_LD(self, tok):
        tok = self._next_token()
        if tok == '(':
            tok = self._next_token()
            if tok == 'HL':
                tok = self._next_token()
                if tok == ')':
                    self._next_expect(',')
                    self._rule_ld_d(self._next_token(), self._destination['(HL)'])
                elif tok == '+':
                    self._next_expect(')')
                    self._rule_ldi_hl(self._next_token())
                elif tok == '-':
                    self._next_expect(')')
                    self._rule_ldd_hl(self._next_token())
                else:
                    self._unexpected(tok)
            elif tok == 'HLI':
                self._next_expect(')')
                self._rule_ldi_hl(self._next_token())
            elif tok == 'HLD':
                self._next_expect(')')
                self._rule_ldd_hl(self._next_token())
            elif tok == 'C':
                self._rule_ld_p_c(self._next_token())
            elif tok in self._r16_1.keys():
                self._next_expect(')')
                self._next_expect(',')
                self._next_expect('A')
                # LD (R),A
                self._out_byte(0x02 | (self._r16_1[tok] << 4))
            else:
                if type(tok) is not int:
                    sym = tok
                    tok = self._parse_int16(tok, self._imem + 1)
                    if not self._resolved:
                        self._warning(f"Symbol '{sym}' is not resolved at this time. Generated code may be suboptimal. Consider using LDH if {sym} >= $FF00.")
                if tok == 0xFF00:
                    tok = self._next_token()
                    if tok == '+':
                        tok = self._next_token()
                        if tok == 'C':
                            self._rule_ld_p_c(self._next_token())
                        else:
                            tok = self._parse_int8(tok, self._imem + 1)
                            self._rule_ldh_i8(self._next_token(), tok)
                    elif tok == ')':
                        self._rule_ldh_i8_p(self._next_token(), 0)
                    else:
                        self._unexpected(tok)
                elif tok > 0xFF00:
                    self._rule_ldh_i8(self._next_token(), tok & 0xFF)
                else:
                    addr = tok
                    self._next_expect(')')
                    self._next_expect(',')
                    tok = self._next_token()
                    if tok == 'A':
                        # LD (N),A
                        self._out_byte(0xEA)
                        self._out_word(addr)
                    elif tok == 'SP':
                        # LD (N),SP
                        self._out_byte(0x08)
                        self._out_word(addr)
                    else:
                        self._unexpected(tok)
        elif tok == 'HL':
            self._next_expect(',')
            tok = self._next_token()
            if tok == 'SP':
                tok = self._next_token()
                if tok != '+' and tok != '-':
                    self._error(f"Expected '+' or '-', found '{tok}'")
                tok = self._parse_int8(tok, self._imem + 1)
                self._pred_ldhl_sp_n(tok)
            else:
                tok = self._parse_int16(tok, self._imem + 1)
                self._pred_ld_r_n(self._r16_2['HL'], tok)
        elif tok in self._r16_2.keys():
            r16_2 = self._r16_2[tok]
            self._next_expect(',')
            i16 = self._parse_int16(self._next_token(), self._imem + 1)
            self._pred_ld_r_n(r16_2, i16)
        elif tok == 'A':
            self._next_expect(',')
            tok = self._next_token()
            if tok == '(':
                tok = self._next_token()
                if tok == 'HL':
                    tok = self._next_token()
                    if tok == ')':
                        # LD A,(HL)
                        self._pred_ld_d_d(self._destination['A'], self._destination['(HL)'])
                    elif tok == '+':
                        self._next_expect(')')
                        # LD A,(HL+)
                        self._pred_ldi_a_hl()
                    elif tok == '-':
                        self._next_expect(')')
                        # LD A,(HL-)
                        self._pred_ldd_a_hl()
                    else:
                        self._unexpected(tok)
                elif tok == 'HLI':
                    self._next_expect(')')
                    # LD A,(HLI)
                    self._pred_ldi_a_hl()
                elif tok == 'HLD':
                    self._next_expect(')')
                    # LD A,(HLD)
                    self._pred_ldd_a_hl()
                elif tok in self._r16_1.keys():
                    self._next_expect(')')
                    # LD A,(R)
                    self._out_byte(0x0A | (self._r16_1[tok] << 4))
                elif tok == 'C':
                    self._rule_ld_a_c(self._next_token())
                else:
                    if type(tok) is not int:
                        sym = tok
                        tok = self._parse_int16(tok, self._imem + 1)
                        if not self._resolved:
                            self._warning(f"Symbol '{sym}' is not resolved at this time. Generated code may be suboptimal. Consider using LDH if {sym} >= $FF00.")
                    if tok == 0xFF00:
                        tok = self._next_token()
                        if tok == '+':
                            tok = self._next_token()
                            if tok == 'C':
                                self._rule_ld_a_c(self._next_token())
                            else:
                                i8 = self._parse_int8(tok, self._imem + 1)
                                self._rule_ldh_a_i8(self._next_token(), i8)
                        elif tok == ')':
                            self._pred_ldh_a_n(0)
                        else:
                            self._unexpected(tok)
                    elif tok > 0xFF00:
                        self._next_expect(')')
                        self._pred_ldh_a_n(tok & 0xFF)
                    else:
                        self._next_expect(')')
                        # LD A,(N)
                        self._out_byte(0xFA)
                        self._out_word(tok)

            elif tok in self._r8:
                self._pred_ld_d_d(self._destination['A'], self._destination[tok])
            else:
                self._unexpected(tok)
        elif tok in self._r8:
            self._next_expect(',')
            self._rule_ld_d(self._next_token(), self._destination[tok])
        else:
            self._unexpected(tok)
        self._next_token()

    def _rule_ld_d(self, tok, dest1):
        if tok == '(':
            self._next_expect('HL')
            self._next_expect(')')
            self._pred_ld_d_d(dest1, self._destination['(HL)'])
        elif tok in self._r8:
            self._pred_ld_d_d(dest1, self._destination[tok])
        else:
            # LD D,N
            self._out_byte(0x06 | (dest1 << 3))
            tok = self._parse_int8(tok)
            self._out_byte(tok)

    def _pred_ld_d_d(self, dest1, dest2):
        # LD D,D
        self._out_byte(0x40 | (dest1 << 3) | dest2)

    def _rule_ldi_hl(self, tok):
        self._expect(tok, ',')
        self._next_expect('A')
        # LDI (HL),A
        # LD (HLI),A
        # LD (HL+),A
        self._out_byte(0x22)

    def _rule_ldd_hl(self, tok):
        self._expect(tok, ',')
        self._next_expect('A')
        # LDD (HL),A
        # LD (HLD),A
        # LD (HL+-,A
        self._out_byte(0x32)

    def _rule_ld_p_c(self, tok):
        self._expect(tok, ')')
        self._next_expect(',')
        self._next_expect('A')
        # LD (C),A
        # LD (FF00+C),A
        self._out_byte(0xE2)

    def _rule_ldh_i8(self, tok, i8):
        self._expect(tok, ')')
        self._rule_ldh_i8_p(self._next_token(), i8)

    def _rule_ldh_i8_p(self, tok, i8):
        self._expect(tok, ',')
        self._expect('A')
        # LD (FF00+N),A
        # LDH (N),A
        self._out_byte(0xE0)
        self._out_byte(i8)

    def _pred_ldhl_sp_n(self, i8):
        # LDHL SP,N
        # LD HL,SP+N
        self._out_byte(0xF8)
        self._out_byte(i8)

    def _pred_ld_r_n(self, r16_2, i16):
        self._out_byte(0x01 | (r16_2 << 4))
        self._out_word(i16)

    def _pred_ldi_a_hl(self):
        self._out_byte(0x2A)

    def _pred_ldd_a_hl(self):
        self._out_byte(0x3A)

    def _rule_ld_a_c(self, tok):
        self._expect(tok, ')')
        # LD A,(C)
        self._out_byte(0xF2)

    def _rule_ldh_a_i8(self, tok, i8):
        self._expect(tok, ')')
        self._pred_ldh_a_n(i8)

    def _pred_ldh_a_n(self, i8):
        # LD A,(FF00+N)
        # LDH A,(N)
        self._out_byte(0xF0)
        self._out_byte(i8)

    def _parse_LDD(self, tok):
        if tok == 'A':
            self._next_expect(',')
            self._next_expect('(')
            self._next_expect('HL')
            self._next_expect(')')
            self._pred_ldd_a_hl()
        elif tok == '(':
            self._next_expect('HL')
            self._next_expect(')')
            self._rule_ldd_hl(self._next_token())
        else:
            self._unexpected(tok)

    def _parse_LDI(self, tok):
        if tok == 'A':
            self._next_expect(',')
            self._next_expect('(')
            self._next_expect('HL')
            self._next_expect(')')
            self._pred_ldi_a_hl()
        elif tok == '(':
            self._next_expect('HL')
            self._next_expect(')')
            self._rule_ldi_hl(self._next_token())
        else:
            self._unexpected(tok)

    def _parse_LDH(self, tok):
        if tok == 'A':
            self._next_expect(',')
            self._next_expect('(')
            i8 = self._parse_int8(self._next_token(), self._imem + 1)
            self._rule_ldh_a_i8(self._next_token(), i8)
        elif tok == '(':
            i8 = self._parse_int8(self._next_token(), self._imem + 1)
            self._rule_ldh_i8(self._next_token(), i8)
        else:
            self._unexpected(tok)

    def _parse_LDHL(self, tok):
        self._expect('SP')
        self._next_expect(',')
        i8 = self._parse_int8(self._next_token, self._imem + 1)
        self._pred_ldhl_sp_n(i8)