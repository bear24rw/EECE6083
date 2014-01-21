#! /usr/bin/env python

from tokens import Tokens
from color import Color

class Symbol:

    current_addr = 0

    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.addr = Symbol.current_addr
        self.used = False

        Symbol.current_addr += 1

    def __repr__(self):
        return "<%r, %r, %r>" % (self.name, self.type, self.addr)

class ParseError(Exception):
    def __init__(self, message, token=None):
        self.message = message
        self.token = token

class Parser:

    def __init__(self, scanner, gen):

        self.has_errors = False
        self.global_symbols = {}
        self.matched_token = None
        self.token = None

        self.gen = gen
        self.scanner = scanner
        self.tokens = scanner.token_iter()
        self.get_next_token()

    def warning(self, message, token=None):

        self.print_message(message, label="warning", token=token, color=Color.YELLOW)

    def error(self, message, token=None):

        self.has_errors = True
        self.print_message(message, label="error", token=token, color=Color.RED)

    def print_message(self, message, label="info", token=None, color=Color.WHITE):

        if token is None:
            token = self.token

        col_num = token.col_num
        line_num = token.line_num
        filename = token.filename
        line_str = token.line_str

        print Color.BOLD + Color.WHITE + "%s:%s:%s: " % (filename, line_num, col_num) + color + "%s: " % label + Color.WHITE + message
        print Color.DEFAULT + line_str
        print Color.GREEN + "%s^" % (' '*(col_num-1)) + Color.DEFAULT

    def get_next_token(self):
        self.prev_token = self.token
        self.token = next(self.tokens)

        # skip the special new line tokens
        while self.token.value == '\n':
            self.token = next(self.tokens)

        #print "Current token: <%s,%r>" % (self.token.type, self.token.value)

    def match(self, type, value=None):
        #print "Trying to match <%s> with <%s>" % (type, self.token.type)
        if self.token.type == type:
            #print "Match successful"
            if value:
                if self.token.value == value:
                    self.matched_token = self.token
                    self.get_next_token()
                    return True
                else:
                    return False
            else:
                value = self.token.value
                self.matched_token = self.token
                self.get_next_token()
                return value
        else:
            #self.error("Could not match token. Found <%s,%r> but expected <%s,%r>." % (self.token.type, self.token.value, type, value))
            return False

    def skip_line(self):
        """
        Skips over a line in the token stream
        This is useful to try and recover from errors
        """
        while self.token.value != '\n':
            self.token = next(self.tokens)

        # at this point the current token in '\n' so just skip to the next one
        self.token = next(self.tokens)

    def program(self):
        """
        <program> ::= <program_header><program_body>
        """
        self.program_header()
        self.program_body()
        print "Finished Parsing"

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

        while True:

            if self.match(Tokens.Type.KEYWORD, 'begin'):
                break

            try:
                self.declaration()
            except ParseError as e:
                self.error(e.message, e.token)
                self.skip_line()
                continue

            if not self.match(Tokens.Type.SYMBOL, ';'):
                self.error("expected ';' after declaration", token=self.prev_token)
                continue

            # don't use match() since it might iterate past end
            if self.token.type == Tokens.Type.SPECIAL and self.token.value == 'EOF':
                break

        while True:

            if self.match(Tokens.Type.KEYWORD, 'end'):
                break

            try:
                self.statement()
            except ParseError as e:
                self.error(e.message, e.token)
                self.skip_line()
                continue

            if not self.match(Tokens.Type.SYMBOL, ";"):
                self.error("expected ';' after statement ", token=self.prev_token)
                continue

            # don't use match() since it might iterate past end
            if self.token.type == Tokens.Type.SPECIAL and self.token.value == 'EOF':
                break


        if not self.match(Tokens.Type.KEYWORD, "program"):
            self.error("expected 'program' but found '%s'" % self.token.value)

    def declaration(self):
        """
        <declaration> ::= [global] <procedure_declaration> |
                          [global] <variable_declaration>
        """

        if self.match(Tokens.Type.KEYWORD, 'global'):
            is_global = True
        else:
            is_global = False

        is_var = self.variable_declaration(is_global)
        is_pro = self.procedure_declaration(is_global)

        if not is_var and not is_pro:
            raise ParseError("expected variable or procedure declaration")

    def procedure_declaration(self, isglobal):
        return False

    def variable_declaration(self, isglobal):
        """
        <variable_declaration> ::= <type_mark><identifier>
                                   [[<array_size>]]
        """

        typemark = self.type_mark()
        if not typemark:
            return False

        name = self.match(Tokens.Type.IDENTIFIER)
        if not name:
            raise ParseError("expected identifier but found '%s'" % self.token.type)

        if isglobal:

            if name in self.global_symbols:
                raise ParseError("duplicate declaration")

            self.global_symbols[name] = Symbol(name, typemark)

        return True

    def type_mark(self):
        """
        <type_mark> ::= integer|float|bool|string
        """
        if self.match(Tokens.Type.KEYWORD, 'integer'): return Tokens.Type.INTEGER
        if self.match(Tokens.Type.KEYWORD, 'float'): return Tokens.Type.FLOAT
        if self.match(Tokens.Type.KEYWORD, 'bool'): return Tokens.Type.BOOL
        if self.match(Tokens.Type.KEYWORD, 'string'): return Tokens.Type.STRING
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

        dest_name, dest_addr, dest_type = self.destination()
        if dest_addr is None:
            return False

        if not self.match(Tokens.Type.SYMBOL, ':='):
            return False

        exp_addr, exp_type = self.expression()

        if exp_addr is None:
            return False

        if dest_type != exp_type:
            raise ParseError("cannot assign expression of type '%s' to destination of type '%s'" % (exp_type, dest_type))

        self.gen.write("M[%s] = R[%s]" % (dest_addr, exp_addr))
        self.global_symbols[dest_name].used = True

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

        if not name in self.global_symbols:
            raise ParseError("destination identifier undefined", self.prev_token)

        return (name, self.global_symbols[name].addr, self.global_symbols[name].type)

    def expression(self):
        """
        <expression> ::=   <expression> & <arith_op>
                         | <expression> | <arith_op>
                         | [not] <arith_op>
        """
        hasnot =  self.match(Tokens.Type.KEYWORD, 'not')

        addr_1, type_1 = self.arith_op()

        if hasnot:
            addr_1 = self.gen.set_new_reg("~R[%d]" % addr_1)

        while self.match(Tokens.Type.SYMBOL, '&') or self.match(Tokens.Type.SYMBOL, '|'):
            operation = self.matched_token.value
            addr_2, type_2 = self.arith_op()
            if type_1 != type_2:
                raise ParseError("expression type error. '%s' and '%s' incompatible." % (type_1, type_2))
            addr_1 = self.gen.set_new_reg("R[%d] %s R[%d]" % (addr_1, operation, addr_2))

        return (addr_1, type_1)

    def arith_op(self):
        """
        <arith_op> ::=   <arith_op> + <relation>
                       | <arith_op> - <relation>
                       | <relation>

        Returns the register address and type of the result: (register_address, type)
        """

        addr_1, type_1 = self.relation()

        while self.match(Tokens.Type.SYMBOL, '+') or self.match(Tokens.Type.SYMBOL, '-'):
            operation = self.matched_token.value
            addr_2, type_2 = self.relation()
            if type_1 != type_2:
                raise ParseError("arith_op type error. '%s' and '%s' incompatible." % (type_1, type_2))
            addr_1 = self.gen.set_new_reg("R[%d] %s R[%d]" % (addr_1, operation, addr_2))

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

        addr_1, type_1 = self.term()

        while self.match(Tokens.Type.SYMBOL, '<')  or \
              self.match(Tokens.Type.SYMBOL, '>=') or \
              self.match(Tokens.Type.SYMBOL, '<=') or \
              self.match(Tokens.Type.SYMBOL, '>')  or \
              self.match(Tokens.Type.SYMBOL, '==') or \
              self.match(Tokens.Type.SYMBOL, '!='):
            operation = self.matched_token.value
            addr_2, type_2 = self.term()
            if type_1 != type_2:
                raise ParseError("type error. '%s' and '%s' incompatible." % (type_1, type_2))
            addr_1 = self.gen.set_new_reg("R[%d] %s R[%d]" % (addr_1, operation, addr_2))
            type_1 = Tokens.Type.BOOL

        return (addr_1, type_1)

    def term(self):
        """
        <term> ::=   <term> * <factor>
                   | <term> / <factor>
                   | <factor>
        """

        addr_1, type_1 = self.factor()

        while self.match(Tokens.Type.SYMBOL, '*') or self.match(Tokens.Type.SYMBOL, '/'):
            operation = self.matched_token.value
            addr_2, type_2 = self.factor()
            if type_1 != type_2:
                raise ParseError("type error. '%s' and '%s' incompatible." % (type_1, type_2))
            addr_1 = self.gen.set_new_reg("R[%d] %s R[%d]" % (addr_1, operation, addr_2))

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
            addr, type = self.expression()
            if not self.match(Tokens.Type.SYMBOL, ')'):
                raise ParseError("expected ')'")
            return (addr, type)

        if self.match(Tokens.Type.SYMBOL, '-'):
            negate = True
        else:
            negate = False

        """
        Identifiers
        """
        if self.match(Tokens.Type.IDENTIFIER):

            name = self.matched_token.value

            if not name in self.global_symbols:
                raise ParseError("undefined identifier", token=self.prev_token)

            if not self.global_symbols[name].used:
                self.warning("variable '%s' is uninitialized when used here" % name, token=self.prev_token)

            addr = self.gen.set_new_reg("M[%d]" % self.global_symbols[name].addr)

            if negate:
                addr = self.gen.set_new_reg("-1 * R[%d]" % addr)

            return (addr, self.global_symbols[name].type)

        """
        Numbers
        """
        if self.match(Tokens.Type.INTEGER) or self.match(Tokens.Type.FLOAT):
            addr = self.gen.set_new_reg(self.matched_token.value)
            if negate:
                addr = self.gen.set_new_reg("-1 * R[%d]" % addr)
            return (addr, self.matched_token.type)

        """
        String
        """
        if self.match(Tokens.Type.STRING): return self.matched_token

        """
        Bool
        """
        if self.match(Tokens.Type.BOOL):
            value = self.matched_token.value
            if value == 'true':
                addr = self.gen.set_new_reg("1")
            else:
                addr = self.gen.set_new_reg("0")
            return (addr, Tokens.Type.BOOL)

        raise ParseError("expected factor but found '%s'" % self.token.value)

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

    if scanner.has_errors or parser.has_errors:
        print "-"*50
        print "BUILD FAILED"
        sys.exit(1)

    print ""
    print "Global Symbols"
    print "-"*50
    for x in parser.global_symbols:
        print parser.global_symbols[x]

    print ""
    print "Program:"
    print "-"*50
    for line in gen.lines:
        print line
