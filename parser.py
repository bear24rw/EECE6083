#! /usr/bin/env python

from contextlib import contextmanager
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


# scan error is raised when the parser encounters an invalid token
class ScanError(Exception): pass

class ParseError(Exception):
    def __init__(self, message, token=None, after_token=False):
        self.message = message
        self.token = token
        self.after_token = after_token

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

    def error(self, message, token=None, after_token=False):

        self.has_errors = True
        self.print_message(message, label="error", token=token, after_token=after_token, color=Color.RED)

    def print_message(self, message, label="info", token=None, after_token=False, color=Color.WHITE):

        if token is None:
            token = self.token

        col_num = token.col_num
        line_num = token.line_num
        filename = token.filename
        line_str = token.line_str

        # calculate the start of the printed mark by ignoring all leading whitespace
        mark_start = col_num - (len(line_str) - len(line_str.lstrip()))
        mark_length = len(token.value)

        # check if we want to place the mark right after the token
        if after_token:
            mark_start = mark_start + mark_length
            mark_length = 1

        print Color.BOLD + Color.WHITE + "%s:%s:%s: " % (filename, line_num, col_num) + color + "%s: " % label + Color.WHITE + message
        print Color.DEFAULT + line_str.strip()
        print Color.GREEN + "%s^%s" % (' '*(mark_start-1), '~'*(mark_length-1)) + Color.DEFAULT

    def get_next_token(self):

        self.prev_token = self.token

        while True:
            self.token = next(self.tokens)
            if self.token.type == Tokens.INVALID:
                raise ScanError
            if self.token.type == Tokens.COMMENT:
                continue
            if self.token.value == '\n':
                continue
            break

        #print "Current token: <%s,%r>" % (self.token.type, self.token.value)

    def match(self, type, value=None):

        # If this isn't even the right type of token just return
        if self.token.type != type:
            #self.error("Could not match token. Found <%s,%r> but expected <%s,%r>." % (self.token.type, self.token.value, type, value))
            return False

        # If we're only looking for a certain type just return the value
        if value is None:
            value = self.token.value
            self.matched_token = self.token
            self.get_next_token()
            return value

        # If we're looking for a certain value as well then return if we matched it
        if self.token.value == value:
            self.matched_token = self.token
            self.get_next_token()
            return True

        return False

    def skip_until(self, find, consume=False):
        """
        Skips tokens until we hit the token with value 'find'
        """
        # TODO: handle scanner errors, EOF

        if isinstance(find, str):
            find = [find]

        while self.token.value not in find:
            self.token = next(self.tokens)

        if consume:
            self.token = next(self.tokens)


    def skip_line(self):
        """
        Skips over a line in the token stream
        """
        self.skip_until('\n', consume=True)

    @contextmanager
    def resync(self, find=None, consume=False, at_next_token=False):
        try:
            yield
        except ParseError as e:
            self.error(e.message, e.token, e.after_token)
            if at_next_token: self.get_next_token()
            if find: self.skip_until(find, consume)
        except ScanError as e:
            if at_next_token: self.get_next_token()
            if find: self.skip_until(find, consume)

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
        self.match(Tokens.KEYWORD, "program")
        name = self.match(Tokens.IDENTIFIER)
        self.match(Tokens.KEYWORD, "is")

    def program_body(self):
        """
        <program_body> ::= (<declaration>;)*
                           begin
                               (<statement>;)*
                           end program
        """

        self.declarations()

        self.match(Tokens.KEYWORD, 'begin')

        self.statements()

        if not self.match(Tokens.KEYWORD, "program"):
            self.error("expected 'program' but found '%s'" % self.token.value)

    def declaration(self):
        """
        <declaration> ::= [global] <procedure_declaration> |
                          [global] <variable_declaration>
        """

        if self.match(Tokens.KEYWORD, 'global'):
            is_global = True
        else:
            is_global = False

        if self.procedure_declaration(is_global):
            return

        if self.variable_declaration(is_global):
            return

        raise ParseError("expected variable or procedure declaration")

    def declarations(self):
        """
        Helper function to process multiple lines of delcarations
        """

        while self.token.value not in ('EOF', 'begin'):

            with self.resync('\n'):
                self.declaration()

            if not self.match(Tokens.SYMBOL, ';'):
                self.error("expected ';' after declaration", self.prev_token, after_token=True)
                continue


    def procedure_declaration(self, isglobal):
        """
        <procedure_declaration> ::= <procedure_header><procedure_body>
        """
        if not self.procedure_header(isglobal):
            return False
        self.procedure_body()
        return True

    def procedure_body(self):
        """
        <procedure_body> ::= (<declaration>;)*
                             begin
                                (<statement>;)*
                             end procedure
        """

        self.declarations()

        self.match(Tokens.KEYWORD, 'begin')

        self.statements()

        if not self.match(Tokens.KEYWORD, "procedure"):
            self.error("expected 'procedure' but found '%s'" % self.token.value)


    def procedure_header(self, isglobal):
        """
        <procedure_header> ::= procedure <identifier> ([<parameter_list>])
        """

        if not self.match(Tokens.KEYWORD, 'procedure'):
            return False

        name = self.match(Tokens.IDENTIFIER)
        if not name:
            self.error("expected procedure identifier")

        if not self.match(Tokens.SYMBOL, '('):
            self.error("expected '('")

        self.parameter_list()

        if not self.match(Tokens.SYMBOL, ')'):
            self.error("expected ')' or ','", self.prev_token, after_token=True)
            self.skip_line()

        return True

    def parameter_list(self):
        """
        <parameter_list> ::= <parameter>,<parameter_list> |
                             <parameter>
        """

        with self.resync((',',')')):
            self.parameter()

        if self.match(Tokens.SYMBOL, ','):
            self.parameter_list()

        return False

    def parameter(self):
        """
        <parameter> ::= <variable_declaration> (in|out)
        """

        self.variable_declaration()

        if self.token.type != Tokens.KEYWORD:
            raise ParseError("expected keyword 'in' or 'out'", self.token)

        if self.token.value not in ('in', 'out'):
            raise ParseError("expected 'in' or 'out' following variable", self.token)

        isin = self.match(Tokens.KEYWORD, 'in')

        if not isin:
            isout = self.match(Tokens.KEYWORD, 'out')

        return True

    def variable_declaration(self, isglobal=False):
        """
        <variable_declaration> ::= <type_mark><identifier>
                                   [[<array_size>]]
        """

        typemark = self.type_mark()

        name = self.match(Tokens.IDENTIFIER)
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
        if self.match(Tokens.KEYWORD, 'integer'): return Tokens.INTEGER
        if self.match(Tokens.KEYWORD, 'float'): return Tokens.FLOAT
        if self.match(Tokens.KEYWORD, 'bool'): return Tokens.BOOL
        if self.match(Tokens.KEYWORD, 'string'): return Tokens.STRING
        raise ParseError("expected type mark")

    def statement(self):
        """
        <statement> ::= <assignment_statement>
                        | <if_statement>
                        | <loop_statement>
        """
        if self.if_statement():         return 'if'
        if self.loop_statement():       return 'loop'
        if self.assignment_statement(): return 'assignment'
        raise ParseError("invalid statement")

    def statements(self):
        """
        Helper function to process multiple lines of statements
        """

        while self.token.value not in ('EOF', 'else', 'end'):

            with self.resync('\n', consume=True):
                self.statement()

                if not self.match(Tokens.SYMBOL, ";"):
                    self.error("expected ';' after statement ", token=self.prev_token, after_token=True)

        # consume the 'end' token if there is one
        self.match(Tokens.KEYWORD, 'end')


    def assignment_statement(self):
        """
        <assignment_statement> ::= <destination> := <expression>
        """

        dest_name, dest_addr, dest_type = self.destination()

        # if the next token is not an assignment operator we are
        # not doing an assignment so just return
        if not self.match(Tokens.SYMBOL, ':='):
            return False

        # we are doing an assignment but the destination was invalid
        if dest_addr is None:
            raise ParseError("destination identifier undefined", self.prev_token)

        self.global_symbols[dest_name].used = True

        exp_addr, exp_type = self.expression()

        if exp_addr is None:
            return False

        if dest_type != exp_type:
            raise ParseError("cannot assign expression of type '%s' to destination of type '%s'" % (exp_type, dest_type), self.prev_token)

        self.gen.write("M[%s] = R[%s]" % (dest_addr, exp_addr))

        return True

    def if_statement(self):
        """
        <if_statement> ::= if(<expression>)then
                            (<statement>;)+
                            [else(<statement>;)+]
                            end if
        """

        # if the first keyword isn't 'if' dont even try to continue
        if not self.match(Tokens.KEYWORD, 'if'):
            return False

        if not self.match(Tokens.SYMBOL, '('):
            self.error("expected '(' after 'if'")

        # generate two labels to use for jumping to the
        # else block and the end of the if block
        else_label = self.gen.new_label()
        end_label = self.gen.new_label()

        exp_addr, exp_type = None, None

        # if the expression fails try to find either the right paren or a new line
        with self.resync([')', '\n']):

            exp_addr, exp_type = self.expression()

            if exp_type != Tokens.BOOL:
                raise ParseError("expression must evaluate to type boolean")

        if not self.match(Tokens.SYMBOL, ')'):
            self.erro("expected ')' after expression", self.prev_token)

        if not self.match(Tokens.KEYWORD, 'then'):
            self.error("expected 'then'", self.prev_token)

        # if the branch is not taken jump to the else
        self.gen.write("if(R[%s] == 0) { goto %s; }" % (exp_addr, else_label))

        # process the body of the if block
        self.statements()

        self.gen.goto_label(end_label)
        self.gen.put_label(else_label)

        # if there is an else block process that too
        if self.match(Tokens.KEYWORD, 'else'):
            self.statements()

        self.gen.put_label(end_label)

        if not self.match(Tokens.KEYWORD, 'if'):
            raise ParseError("expected 'if'")

        return True

    def loop_statement(self):
        """
        <loop_statement> ::= for(<assignment_statement>; <expression>)
                             (<statement>;)*
                             end for
        """

        # if the first keyword isn't 'for' dont even try to continue
        if not self.match(Tokens.KEYWORD, 'for'):
            return False

        if not self.match(Tokens.SYMBOL, '('):
            self.error("expected '(' after 'for'")

        loop_label = self.gen.new_label()
        end_label = self.gen.new_label()

        self.gen.put_label(loop_label)

        with self.resync('\n', consume=True):

            if not self.assignment_statement():
                raise ParseError("expected assignment statement")

            if not self.match(Tokens.SYMBOL, ';'):
                raise ParseError("expected ';' after statement", self.prev_token)

            exp_addr, _ = self.expression()
            if exp_addr is None:
                raise ParseError("invalid expression")

            self.gen.write("if (R[%d] == 0) { goto %s; }" % (exp_addr, end_label))

            if not self.match(Tokens.SYMBOL, ')'):
                raise ParseError("expected closing ')' but found '%r'" % self.token, self.prev_token, after_token=True)

        # consume the body of the loop
        self.statements()

        if not self.match(Tokens.KEYWORD, 'for'):
            self.error("expected 'for'")

        self.gen.goto_label(loop_label)
        self.gen.put_label(end_label)

        return True

    def destination(self):
        """
        <destination> ::= <identifier>[[<expression>]]
        """

        name = self.match(Tokens.IDENTIFIER)

        if not name in self.global_symbols:
            return (name, None, None)

        return (name, self.global_symbols[name].addr, self.global_symbols[name].type)

    def operation(self, lhs, operations, rhs, result_is_bool=False):
        """
        Helper function to perform the generic function: R[x] op R[y]
        'lhs' is a 2-tuple containing the (register_addr, type) for the left hand side of the operator
        'rhs' is the function to handle the right hand side of the operator
        'operations' contains a list of valid operator symbols
        'result_is_bool' is set to true if the operation results in a boolean
        """

        lhs_addr, lhs_type = lhs

        while any([self.match(Tokens.SYMBOL, op) for op in operations]):
            operation = self.matched_token.value
            rhs_addr, rhs_type = rhs()
            if lhs_type != rhs_type:
                raise ParseError("expression type error. '%s' and '%s' incompatible." % (lhs_type, rhs_type), self.prev_token)
            lhs_addr = self.gen.set_new_reg("R[%d] %s R[%d]" % (lhs_addr, operation, rhs_addr))
            if result_is_bool:
                lhs_type = Tokens.BOOL

        return (lhs_addr, lhs_type)

    def expression(self):
        """
        <expression> ::=   <expression> & <arith_op>
                         | <expression> | <arith_op>
                         | [not] <arith_op>
        """

        hasnot =  self.match(Tokens.KEYWORD, 'not')

        addr, type = self.arith_op()

        if hasnot:
            addr = self.gen.set_new_reg("~R[%d]" % addr)

        return self.operation((addr, type), ('&', '|'), self.arith_op)

    def arith_op(self):
        """
        <arith_op> ::=   <arith_op> + <relation>
                       | <arith_op> - <relation>
                       | <relation>

        """
        lhs = self.relation()
        return self.operation(lhs, ('+', '-'), self.relation)

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
        lhs = self.term()
        ops = ('<', '>=', '<=', '>', '==', '!=')
        return self.operation(lhs, ops, self.term, result_is_bool=True)


    def term(self):
        """
        <term> ::=   <term> * <factor>
                   | <term> / <factor>
                   | <factor>
        """
        lhs = self.factor()
        return self.operation(lhs, ('*', '/'), self.factor)


    def factor(self):
        """
        <factor> ::=   (<expression>)
                     | [-]<name>
                     | [-]<number>
                     | <string>
                     | true
                     | false

        Trys to find a valid factor and loads it into a register
        Returns a tuple: (register_addr, type)
        """

        if self.match(Tokens.SYMBOL, '('):
            addr, type = self.expression()
            if not self.match(Tokens.SYMBOL, ')'):
                raise ParseError("expected ')'")
            return (addr, type)

        if self.match(Tokens.SYMBOL, '-'):
            negate = True
        else:
            negate = False

        """
        Identifiers
        """
        if self.match(Tokens.IDENTIFIER):

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
        if self.match(Tokens.INTEGER) or self.match(Tokens.FLOAT):
            addr = self.gen.set_new_reg(self.matched_token.value)
            if negate:
                addr = self.gen.set_new_reg("-1 * R[%d]" % addr)
            return (addr, self.matched_token.type)

        """
        String
        """
        if self.match(Tokens.STRING): return self.matched_token

        """
        Bool
        """
        if self.match(Tokens.BOOL):
            value = self.matched_token.value
            if value == 'true':
                addr = self.gen.set_new_reg("1")
            else:
                addr = self.gen.set_new_reg("0")
            return (addr, Tokens.BOOL)

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
