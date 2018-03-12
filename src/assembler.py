'''
Assembler
'''

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
    _directives = {'ORG','BYTE','WORD','ALIGN'}
    _keywords = {'ADC','ADD','AND','BIT','CALL','CCF','CP','CPL','DAA','DEC','DI','EI','HALT','INC','JP','JR',
        'LD','LDD','LDH','LDI','NOP','OR','POP','PUSH','RES','RET','RETI','RL','RLA','RLC','RLCA','RR','RRA',
        'RRC','RRCA','RST','SBC','SCF','SET','SLA','SRA','SRL','STOP','SUB','SWAP','XOR'}
    _r8 = {'A','B','C','D','E','H','L'}
    _r16 = {'BC','DE','HL'}
    _cc = {'Z','NZ','C','NC'}
    _special = {'HLD', 'HLI'}
    _vec = {0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38}

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
        self._line = 0
        self._col = 0
        self._parse()

    def _error(self, msg):
        raise AssemblerError(self._line, self._col, msg)

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
        _set_word(self._imem, value)
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
                    yield self._set_token( ch + tok )
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
                    #if line[self._col-1] != ch:
                    #    self._error('Unclosed string literal')
                    yield self._set_token( '"' + tok )
                elif ch in ',():+-':
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
            else:
                self._parse_instruction(tok)

    def _parse_directive(self, tok):
        if tok[0] == '.':
            tok = tok[1:].upper()
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
        if type(tok) is int or tok=='-' or tok=='+':
            self._out_byte(self._parse_int(tok))
        elif type(tok) is str and len(tok) > 0 and tok[0] == '"':
            for c in tok[1:]:
                self._out_byte(c.encode('latin-1','ignore')[0])
        else:
            self._error(f"Expecting byte constant, found '{tok}'")
        tok = self._next_token()
        if tok == ',':
            self._parse_d_byte(self._next_token())

    def _parse_d_word(self, tok):
        if type(tok) is int or tok == '-' or tok == '+':
            self._out_word(self._parse_int(tok))
        else:
            self._error(f"Expecting word constant, found '{tok}'")
        tok = self._next_token()
        if tok == ',':
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
        tok = tok.upper()
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
        label = label.upper()
        self._labels[label] = value
        self._fill_gaps(label, value)

    def _parse_int(self, tok):
        neg = False
        if tok == '-':
            neg = True
            tok = self._next_token()
        elif tok == '+':
            tok = self._next_token()
        if type(tok) is not int:
            self._error(f"Expecting int constant, found '{tok}'")
        return -tok if neg else tok

    def _parse_int8(self, addr, tok):
        if type(tok) is str and self._is_valid_label(tok):
            tok = tok.upper()
            value = self._labels.get(tok, None)
            if value is None:
                self._gaps8[addr] = tok
                value = 0
            # ...  


    def _fill_gaps(self, label, value):
        getitems = lambda s: map(lambda kv: kv[0], filter(lambda kv: kv[1]==label, s.items()))[:]
        for addr in getitems(self._gaps16):
            self._set_word(addr, value)
            self._gaps16.pop(addr)
        for addr in getitems(self._gaps8):
            self._set_byte(addr, value)
            self._gaps8.pop(addr)

    def _parse_instruction(self, tok):
        tok = tok.upper()
        if tok in self._keywords:
            fn = {
                'ADC': self._parse_ADC,
                'ADD': self._parse_ADD,
                'AND': self._parse_AND,
                'BIT': self._parse_BIT,
                'CALL': self._parse_CALL,
                'CCF': self._parse_CCF,
                'CP': self._parse_CP,
                'CPL': self._parse_CPL,
                'DAA': self._parse_DAA,
                'DEC': self._parse_DEC,
                'DI': self._parse_DI,
                'EI': self._parse_EI,
                'HALT': self._parse_HALT,
                'INC': self._parse_INC,
                'JP': self._parse_JP,
                'JR': self._parse_JR,
                'LD': self._parse_LD,
                'LDD': self._parse_LDD,
                'LDH': self._parse_LDH,
                'LDI': self._parse_LDI,
                'NOP': self._parse_NOP,
                'OR': self._parse_OR,
                'POP': self._parse_POP,
                'PUSH': self._parse_PUSH,
                'RES': self._parse_RES,
                'RET': self._parse_RET,
                'RETI': self._parse_RETI,
                'RL': self._parse_RL,
                'RLA': self._parse_RLA,
                'RLC': self._parse_RLC,
                'RLCA': self._parse_RLCA,
                'RR': self._parse_RR,
                'RRA': self._parse_RRA,
                'RRC': self._parse_RRC,
                'RRCA': self._parse_RRCA,
                'RST': self._parse_RST,
                'SBC': self._parse_SBC,
                'SCF': self._parse_SCF,
                'SET': self._parse_SET,
                'SLA': self._parse_SLA,
                'SRA': self._parse_SRA,
                'SRL': self._parse_SRL,
                'STOP': self._parse_STOP,
                'SUB': self._parse_SUB,
                'SWAP': self._parse_SWAP,
                'XOR': self._parse_XOR,
                }.get(tok)
            fn(self._next_token())
        elif self._is_valid_label(tok):
            if self._next_token() == ':':
                self._next_token()
            self._set_label(tok, self._imem)
        else:
            self._error(f"Expecting instruction, found '{tok}'")

    def _expect(self, tok, expected):
        if tok.upper() != expected:
            self._error(f"Expecting '{expected}', found '{tok}'")

    def _parse_ADC(self, tok):
        self._expect(tok, 'A')
        self._expect(self._next_token(), ',')
        tok = self._next_token()
