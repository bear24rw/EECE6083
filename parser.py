from tokens import Tokens
from color import Color

class Symbol:

    current_addr = 0

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.addr = Symbol.current_addr
        Symbol.current_addr += 1

    def __repr__(self):
        return "<%r, %r, %r>" % (self.name, self.type, self.addr)

class Parser:

    def __init__(self, scanner, gen):
        self.gen = gen
        self.scanner = scanner
        self.tokens = scanner.token_iter()
        self.get_next_token()

        self.global_symbols = {}

    def warning(self, message):

        self.print_message(message, "warning", color=Color.YELLOW)

    def error(self, message):

        self.has_error = True
        self.print_message(message, "error", color=Color.RED)

    def print_message(self, message, label="info", color=Color.WHITE):

        col_num = self.token.col_num
        line_num = self.token.line_num
        filename = self.token.filename
        line_str = self.token.line_str.strip()


        print Color.BOLD + Color.WHITE + "%s:%s:%s: " % (filename, line_num, col_num) + color + "%s: " % label + Color.WHITE + message
        print Color.DEFAULT + line_str
        print Color.GREEN + "%s^" % (' '*(col_num-1)) + Color.DEFAULT

    def get_next_token(self):
        self.token = next(self.tokens)
        print "Current token: <%s,%r>" % (self.token.type, self.token.value)

    def match(self, type, value=None):
        #print "Trying to match <%s> with <%s>" % (type, self.token.type)
        if self.token.type == type:
            #print "Match successful"
            if value:
                if self.token.value == value:
                    self.get_next_token()
                    return True
                else:
                    return False
            else:
                value = self.token.value
                self.get_next_token()
                return value
        else:
            #self.error("Could not match token. Found <%s,%r> but expected <%s,%r>." % (self.token.type, self.token.value, type, value))
            return None

    def program(self):
        """
        <program> ::= <program_header><program_body>
        """
        self.program_header()
        self.program_body()

    def program_header(self):
        """
        <program_header> ::= program <identifier> is
        """
        self.match(Tokens.Type.KEYWORD, "program")
        name = self.match(Tokens.Type.IDENTIFIER)
        self.match(Tokens.Type.KEYWORD, "is")

    def program_body(self):
        """
        <program_body> ::= (<declaration>;)*
                           begin
                               (<statement>;)*
                           end program
        """

        while self.declaration():
            self.match(Tokens.Type.SYMBOL, ";")

        self.match(Tokens.Type.KEYWORD, "begin")

        while self.statement():
            self.match(Tokens.Type.SYMBOL, ";")

        self.match(Tokens.Type.KEYWORD, "end")
        self.match(Tokens.Type.KEYWORD, "program")

    def declaration(self):
        """
        <declaration> ::= [global] <procedure_declaration> |
                          [global] <variable_declaration>
        """
        if self.match(Tokens.Type.KEYWORD, 'global'):
            isglobal = True
        else:
            isglobal = False

        symbol = self.variable_declaration()
        if not symbol:
            return None

        if isglobal:

            if symbol.name in self.global_symbols:
                self.error("duplicate declaration")
                return None

            self.global_symbols[symbol.name] = symbol

        return True

    def variable_declaration(self):
        """
        <variable_declaration> ::= <type_mark><identifier>
                                   [[<array_size>]]
        """
        typemark = self.type_mark()
        if not typemark:
            return None

        name = self.match(Tokens.Type.IDENTIFIER)
        return Symbol(name, typemark)

    def type_mark(self):
        """
        <type_mark> ::= integer|float|bool|string
        """
        if self.match(Tokens.Type.KEYWORD, 'integer'): return 'integer'
        if self.match(Tokens.Type.KEYWORD, 'float'): return 'float'
        if self.match(Tokens.Type.KEYWORD, 'bool'): return 'bool'
        if self.match(Tokens.Type.KEYWORD, 'string'): return 'string'
        return None

    def statement(self):
        """
        <statement> ::= <assignment_statement>
                        | <if_statement>
                        | <loop_statement>
        """
        if self.assignment_statement(): return True
        if self.if_statement():         return True
        if self.loop_statement():       return True
        return None

    def assignment_statement(self):
        """
        <assignment_statement> ::= <destination> := <expression>
        """

        destination = self.destination()
        if not destination:
            return None

        if not self.match(Tokens.Type.SYMBOL, ':='):
            return None

        exp_addr, exp_type = self.expression()

        self.gen.write("M[%d] = R[%d]" % (destination.addr, exp_addr))

        return True

    def if_statement(self):
        return False
    def loop_statement(self):
        return False

    def destination(self):
        """
        <destination> ::= <identifier>[[<expression>]]
        """

        name = self.match(Tokens.Type.IDENTIFIER)
        if not name:
            return None

        if not self.global_symbols[name]:
            self.error("destination identifier undefined")
            return None

        return self.global_symbols[name]

    def expression(self):
        """
        <expression> ::=   <expression> & <arith_op>
                         | <expression> | <arith_op>
                         | [not] <arith_op>
        """
        return self.arith_op()

    def arith_op(self):
        """
        <arith_op> ::=   <arith_op> + <relation>
                       | <arith_op> - <relation>
                       | <relation>
        """
        addr_1, type_1 = self.relation()

        while self.match(Tokens.Type.SYMBOL, '+'):
            addr_2, type_2 = self.relation()
            if type_1 != type_2:
                self.error("type error")
            addr_1 = self.gen.set_new_reg("R[%d] + R[%d]" % (addr_1, addr_2))

        while self.match(Tokens.Type.SYMBOL, '-'):
            addr_2, type_2 = self.relation()
            if type_1 != type_2:
                self.error("type error")
            addr_1 = self.gen.set_new_reg("R[%d] - R[%d]" % (addr_1, addr_2))

        return (addr_1, type_1)

    def relation(self):
        """
        <relation> ::=   <relation> <  <term>
                       | <relation> >= <term>
                       | <relation> <= <term>
                       | <relation> >  <term>
                       | <relation> == <term>
                       | <relation> != <term>
                       | <term>
        """
        return self.term()

    def term(self):
        """
        <term> ::=   <term> * <factor>
                   | <term> / <factor>
                   | <factor>
        """

        addr_1, type_1 = self.factor()

        while self.match(Tokens.Type.SYMBOL, '*'):
            addr_2, type_2 = self.factor()
            if type_1 != type_2:
                self.error("type error")
            addr_1 = self.gen.set_new_reg("R[%d] * R[%d]" % (addr_1, addr_2))

        while self.match(Tokens.Type.SYMBOL, '/'):
            addr_2, type_2 = self.factor()
            if type_1 != type_2:
                self.error("type error")
            addr_1 = self.gen.set_new_reg("R[%d] / R[%d]" % (addr_1, addr_2))

        return (addr_1, type_1)

    def factor(self):
        """
        <factor> ::=   (<expression>)
                     | [-]<name>
                     | [-]<number>
                     | <string>
                     | true
                     | false

        Returns a 2-tuple containing register
        addr and type: (reg_addr, type)
        """

        if self.match(Tokens.Type.SYMBOL, '('):
            self.expression()
            self.match(Tokens.Type.SYMBOL, ')')
            return

        if self.match(Tokens.Type.SYMBOL, '-'):
            negate = True
        else:
            negate = False

        # save the current token since the
        # match() function might eat it
        token = self.token

        """
        Identifiers
        """
        if self.match(Tokens.Type.IDENTIFIER):
            if not token.value in self.global_symbols:
                self.error("undefined identifier")
                return None
            addr = self.gen.set_new_reg("M[%d]" % self.global_symbols[token.value].addr)
            return (addr, token.type)

        """
        Numbers
        """
        if self.match(Tokens.Type.CONSTANT):
            addr = self.gen.set_new_reg(token.value)
            return (addr, token.type)

        """
        String
        """
        if self.match(Tokens.Type.STRING): return token

        """
        Bool
        """
        if self.match(Tokens.Type.KEYWORD, 'true'): return token
        if self.match(Tokens.Type.KEYWORD, 'false'): return token

        return None

    def name(self):
        """
        <name> ::= <identifier>[[<expression>]]
        """
        pass


if __name__ == "__main__":
    import sys
    from scanner import Scanner
    from gen import Gen
    gen = Gen("/tmp/out.txt")
    scanner = Scanner(sys.argv[1])
    parser = Parser(scanner, gen)
    parser.program()

    print "Global Symbols"
    print "-"*50
    for x in parser.global_symbols:
        print parser.global_symbols[x]

    print ""
    print "Program:"
    print "-"*50
    for line in gen.lines:
        print line
