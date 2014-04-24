#! /usr/bin/env python

from contextlib import contextmanager
from tokens import Tokens
from color import Color

class Symbol:

    def __init__(self, name='', type='', size=1, direction=''):
        self.name = name
        self.type = type
        self.size = size
        self.addr = 0
        self.used = False
        self.params = []
        self.label = name
        self.direction = direction
        self.current_reg = None
        self.indirect = False # M[R[current_reg]]
        self.isglobal = False
        self.isparam = False
        self.isarray = False

    def __repr__(self):
        if self.type == 'procedure':
            return "<%r, %r, params=%r>" % (self.name, self.type, [(x.name, x.type, x.direction) for x in self.params])
        else:
            return "<%r, %r, size=%r, addr=%r>" % (self.name, self.type, self.size, self.addr)


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
        self.matched_token = None
        self.token = None

        self.scope_level = 0
        self.global_symbols = {}
        self.symbols = [{}]
        self.global_addr = 0    # absolute address = global_addr
        self.local_addr = 0     # absolute address = FP + local_addr
        self.current_procedure = None # symbol name of current procedure

        self.gen = gen
        self.scanner = scanner
        self.tokens = scanner.token_iter()
        self.get_next_token()

        # add the built-in function to the symbol table
        self.global_symbols['putinteger'] = Symbol('putinteger')
        self.global_symbols['putinteger'].type = 'procedure'
        self.global_symbols['putinteger'].params.append(Symbol(type="INTEGER", direction="in"))

        self.global_symbols['putbool'] = Symbol('putbool')
        self.global_symbols['putbool'].type = 'procedure'
        self.global_symbols['putbool'].params.append(Symbol(type="BOOL", direction="in"))

        self.global_symbols['putstring'] = Symbol('putstring')
        self.global_symbols['putstring'].type = 'procedure'
        self.global_symbols['putstring'].params.append(Symbol(type="STRING", direction="in"))

        self.global_symbols['putfloat'] = Symbol('putfloat')
        self.global_symbols['putfloat'].type = 'procedure'
        self.global_symbols['putfloat'].params.append(Symbol(type="FLOAT", direction="in"))

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

        # always consume the newlines
        if self.token.value == '\n' and '\n' in find:
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

    def enter_scope(self):
        self.symbols.append({})
        self.scope_level += 1
        self.local_addr = 0

    def exit_scope(self):
        try:
            self.symbols.pop()
            self.scope_level -= 1
        except IndexError:
            self.error("attempted to exit outermost scope")

    def cur_symbols(self):
        """
        Returns a list of symbol names in the current scope
        """
        return self.symbols[-1].keys() + self.global_symbols.keys()

    def add_symbol(self, x, is_global=False):
        """
        Adds a symbol to the current scope
        """
        if is_global:
            self.global_symbols[x.name] = x
            self.global_symbols[x.name].addr = self.global_addr
            self.global_symbols[x.name].isglobal = True
            if x.type != 'procedure':
                self.global_addr += x.size
        else:
            addr = self.local_symbols_size() + self.local_param_size()
            self.symbols[-1][x.name] = x
            self.symbols[-1][x.name].addr = addr

    def local_param_size(self):
        """
        Returns the size in byte of the local paramters
        """
        size = 0
        for s in self.symbols[-1]:
            if self.symbols[-1][s].type == 'procedure': continue
            if not self.symbols[-1][s].isparam: continue
            #if self.symbols[-1][s].isparam: continue
            if self.symbols[-1][s].direction == 'out':
                size += 1
            else:
                size += self.symbols[-1][s].size
        return size

    def local_symbols_size(self):
        """
        Returns the size in bytes of the local symbols
        """
        size = 0
        for s in self.symbols[-1]:
            if self.symbols[-1][s].type == 'procedure': continue
            if self.symbols[-1][s].isparam: continue
            #if self.symbols[-1][s].isparam: continue
            size += self.symbols[-1][s].size
        return size

    def global_symbols_size(self):
        """
        Returns the size in bytes of the global symbols
        """
        size = 0
        for s in self.global_symbols:
            if self.global_symbols[s].type == 'procedure': continue
            size += self.global_symbols[s].size
        return size

    def get_symbol(self, x):
        if x in self.global_symbols:
            return self.global_symbols[x]
        elif x in self.symbols[-1]:
            return self.symbols[-1][x]
        else:
            raise ParseError("Tried to lookup unknown symbol: %r" % x)

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

        self.gen.put_label("main")

        self.gen.comment("starting fp at top of global vars")
        self.gen.set_fp(self.global_symbols_size())

        self.gen.comment("resetting sp to fp")
        self.gen.set_sp_to_fp()

        self.gen.comment("moving sp to top of local vars")
        self.gen.inc_sp(self.local_symbols_size())

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

        if is_global and self.scope_level > 0:
            self.error("global declaration only allowed in outermost scope", self.prev_token)

        if self.procedure_declaration(is_global):
            return

        if self.variable_declaration(is_global):
            return

    def declarations(self):
        """
        Helper function to process multiple lines of declarations
        """

        while self.token.value not in ('EOF', 'begin'):

            with self.resync(['begin', '\n']):
                self.declaration()

                if not self.match(Tokens.SYMBOL, ';'):
                    self.error("expected ';' after declaration", self.prev_token, after_token=True)


    def procedure_declaration(self, is_global):
        """
        <procedure_declaration> ::= <procedure_header><procedure_body>
        """
        name = self.procedure_header(is_global)
        if not name:
            return False
        self.current_procedure = name
        self.procedure_body(name)
        self.exit_scope()
        return True

    def procedure_body(self, name):
        """
        <procedure_body> ::= (<declaration>;)*
                             begin
                                (<statement>;)*
                             end procedure
        """

        self.declarations()

        self.match(Tokens.KEYWORD, 'begin')

        label = self.gen.new_label(name+'_start')
        self.gen.put_label(label)
        self.get_symbol(name).label = label

        #self.gen.comment("setting fp")
        #self.gen.set_fp_to_sp()

        if self.local_symbols_size() > 0:
            self.gen.comment("moving sp to top of local vars")
            self.gen.inc_sp(self.local_symbols_size())

        # map parameter symbol address to point to correct location
        # with in the stack frame
        for i, param in enumerate(reversed(self.get_symbol(name).params)):
            #param.addr = i
            if param.direction == 'out':
                param.indirect = True

        self.gen.comment("statements")
        self.statements()

        self.gen.return_to_caller(self.local_param_size(), self.local_symbols_size())

        if not self.match(Tokens.KEYWORD, "procedure"):
            self.error("expected 'procedure' but found '%s'" % self.token.value)

        # extra new line after each function block
        self.gen.write("", indent="")


    def procedure_header(self, is_global):
        """
        <procedure_header> ::= procedure <identifier> ([<parameter_list>])
        """

        if not self.match(Tokens.KEYWORD, 'procedure'):
            return False

        name = self.match(Tokens.IDENTIFIER)
        if not name:
            self.error("expected procedure identifier")

        symbol = Symbol(name, "procedure")

        if name in self.cur_symbols():
            self.error("identifier already in use")

        # add the symbol to the current (parent) scope
        self.add_symbol(symbol, is_global)

        # enter the new scope and also add it there so we can do recursion we
        # need to do this before parsing the parameters since the parameter
        # function adds symbols to the current scope
        self.enter_scope()
        self.add_symbol(symbol, is_global)

        if not self.match(Tokens.SYMBOL, '('):
            self.error("expected '('")

        if self.token.value != ')':
            symbol.params = self.parameter_list()

        if not self.match(Tokens.SYMBOL, ')'):
            self.error("expected ')' or ','", self.prev_token, after_token=True)
            self.skip_until('\n')

        return name

    def parameter_list(self):
        """
        <parameter_list> ::= <parameter>,<parameter_list> |
                             <parameter>
        """

        params = []

        while True:

            with self.resync((',',')')):
                param = self.parameter()
                params.append(param)

            if not self.match(Tokens.SYMBOL, ','):
                break

        return params

    def parameter(self):
        """
        <parameter> ::= <variable_declaration> (in|out)
        """

        symbol = self.variable_declaration()
        symbol.isparam = True

        if self.token.type != Tokens.KEYWORD:
            raise ParseError("expected keyword 'in' or 'out'", self.token)

        if self.token.value not in ('in', 'out'):
            raise ParseError("expected 'in' or 'out' following variable", self.token)

        if self.token.value == 'in':
            self.match(Tokens.KEYWORD, 'in')
            symbol.direction = 'in'
            symbol.used = True
        else:
            self.match(Tokens.KEYWORD, 'out')
            symbol.direction = 'out'

        return symbol

    def variable_declaration(self, is_global=False):
        """
        <variable_declaration> ::= <type_mark><identifier>
                                   [[<array_size>]]

        Returns the symbol object of the new symbol
        """

        typemark = self.type_mark()

        name = self.match(Tokens.IDENTIFIER)

        if not name:
            raise ParseError("expected identifier", self.prev_token, after_token=True)

        if name in self.cur_symbols():
            raise ParseError("duplicate declaration of '%s'" % name, self.prev_token)

        size = 1
        isarray = False

        if self.match(Tokens.SYMBOL, '['):

            isarray = True

            size = self.match(Tokens.INTEGER)

            if not size:
                raise ParseError("expected positive integer specifying array size")

            if size == '0':
                raise ParseError("array size must be at least 1", self.prev_token)

            if not self.match(Tokens.SYMBOL, ']'):
                raise ParseError("expected closing ']'")

            size = int(size)

        symbol = Symbol(name, typemark, size=size)
        symbol.isarray = isarray
        self.add_symbol(symbol, is_global)

        return symbol

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
                        | <procedure_call>
                        | <return_statement>
        """
        self.gen.comment("statement: %s" % self.token.line_str.strip())
        if self.if_statement():         return
        if self.loop_statement():       return
        if self.procedure_call():       return
        if self.assignment_statement(): return
        if self.return_statement():     return
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

    def return_statement(self):
        """
        <return_statement> ::= return
        """

        if not self.match(Tokens.KEYWORD, "return"):
            return False

        self.gen.return_to_caller(self.local_param_size(), self.local_symbols_size())
        return True

    def procedure_call(self):
        """
        <procedure_call> ::= <identifier>([<argument_list>])
        """

        # don't consume the identifier until we are sure it's
        # a procedure call and not an assignment statement

        name = self.token.value

        if not self.token.type == Tokens.IDENTIFIER:
            return False

        if name is None:
            return False

        # TODO: check if next token is ( so we can throw undefined procedure

        if name not in self.cur_symbols():
            return False

        if self.get_symbol(name).type != "procedure":
            return False

        # we know it's a procedure call so we're safe to consume
        self.get_next_token()

        if not self.match(Tokens.SYMBOL, '('):
            self.error("expected '('")

        self.gen.comment("calling %s" % name)

        args = self.argument_list(name)

        if not self.match(Tokens.SYMBOL, ')'):
            self.error("expected ')' after argument list")

        # generate a label that we will return to after call is complete
        return_label = self.gen.new_label("return_from_%s" % name)

        # push return address onto the stack
        self.gen.comment("pushing return address onto stack")
        reg = self.gen.set_new_reg("(int)&&%s" % return_label)
        self.gen.push_stack(reg)

        # push current frame pointer onto the stack
        self.gen.comment("pushing current FP onto stack")
        reg = self.gen.set_new_reg("FP")
        self.gen.push_stack(reg)

        # new frame for this call
        self.gen.set_fp_to_sp()

        # push the addresses of all arguments onto the stack
        self.gen.comment("pushing args onto stack")
        for i, (addr, _) in enumerate(args):
            self.gen.push_stack(addr)

        #self.gen.increment_fp(len(args)+

        self.gen.goto_label(self.get_symbol(name).label)
        self.gen.put_label(return_label)

        return True

    def argument_list(self, procedure_name):
        """
        <argument_list> ::=   <expression>,<argument_list>
                            | <expression>

        """

        arguments = []
        argument_idx = 0

        while True:

            with self.resync([',', ')', '\n']):

                direction = self.get_symbol(procedure_name).params[argument_idx].direction

                if direction == 'in':
                    """
                    check if argument is an array or an expression
                    """
                    name = self.token.value
                    tok_type = self.token.type

                    exp_addr, exp_type = self.expression()

                    if exp_addr is None:
                        if tok_type == Tokens.IDENTIFIER and self.get_symbol(name).isarray:
                            self.gen.comment("Loading array '%s' into registers" % name)
                            for i in range(self.get_symbol(name).size):
                                if self.get_symbol(name).isglobal:
                                    r = self.gen.set_new_reg("M[%s+%s]" % (self.get_symbol(name).addr, i))
                                else:
                                    r = self.gen.set_new_reg("M[FP+%s+%s]" % (self.get_symbol(name).addr, i))
                                arguments.append((r, self.token.type))
                            exp_type = self.get_symbol(name).type
                        else:
                            raise ParseError("expected array indentifier or expression")
                    else:
                        self.gen.comment("Loaded expression into register")
                        arguments.append((exp_addr, exp_type))
                else:
                    if not self.match(Tokens.IDENTIFIER):
                        raise ParseError("expected out parameter to be an identifier")
                    name = self.matched_token.value
                    if name not in self.cur_symbols():
                        raise ParseError("undefined identifier", token=self.prev_token)

                    self.gen.comment("Loading %s onto stack" % name)
                    # if its not global we need to return the address relative to our current frame pointer
                    if self.get_symbol(name).isparam and self.get_symbol(name).direction == 'out':
                        exp_addr = self.gen.set_new_reg("M[FP+%s]" % self.get_symbol(name).addr)
                    elif self.get_symbol(name).isglobal:
                        exp_addr = self.gen.set_new_reg("M[%s]" % self.get_symbol(name).addr)
                    else:
                        exp_addr = self.gen.set_new_reg("FP + %s" % self.get_symbol(name).addr)

                    exp_type = self.get_symbol(name).type

                    arguments.append((exp_addr, exp_type))

                expected_type = self.get_symbol(procedure_name).params[argument_idx].type
                if exp_type != expected_type:
                    self.error("argument type miss-match. expected '%s' but found '%s'" % (expected_type, exp_type), self.prev_token)

                argument_idx += 1
                # TODO: check number of arguments match

            if not self.match(Tokens.SYMBOL, ','):
                break

        return arguments

    def assignment_statement(self):
        """
        <assignment_statement> ::= <destination> := <expression>
        """

        dest_name, dest_addr, offset_reg, dest_type = self.destination()

        # if the next token is not an assignment operator we are
        # not doing an assignment so just return
        if not self.match(Tokens.SYMBOL, ':='):
            return False

        # we are doing an assignment but the destination was invalid
        if dest_addr is None:
            raise ParseError("destination identifier '%s' undefined" % dest_name, self.prev_token)

        exp_addr, exp_type = self.expression()

        if exp_addr is None:
            return False

        if dest_type != exp_type:
            raise ParseError("cannot assign expression of type '%s' to destination of type '%s'" % (exp_type, dest_type), self.prev_token)

        self.get_symbol(dest_name).current_reg = exp_addr
        self.get_symbol(dest_name).used = True

        if self.get_symbol(dest_name).isglobal:
            self.gen.move_reg_to_mem_global(exp_addr, dest_addr, offset_reg=offset_reg)
            return True

        if self.get_symbol(dest_name).indirect:
            r = self.gen.set_new_reg("M[FP + %d]" % dest_addr)
            if offset_reg:
                r = self.gen.set_new_reg("R[%d] + R[%d]" % (r, offset_reg))
            self.gen.move_reg_to_mem_indirect(reg=exp_addr, mem=r)
        else:
            self.gen.move_reg_to_mem(reg=exp_addr, mem=dest_addr, offset_reg=offset_reg)

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
        else_label = self.gen.new_label('else')
        end_label = self.gen.new_label('endif')

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

        loop_label = self.gen.new_label('for')
        end_label = self.gen.new_label('endfor')

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
        # TODO: return the symbol object

        name_token = self.token
        name = self.match(Tokens.IDENTIFIER)

        if name not in self.cur_symbols():
            return (name, None, None, None)

        offset_addr = None

        if self.match(Tokens.SYMBOL, '['):

            if not self.get_symbol(name).isarray:
                raise ParseError("'%s' is not an array" % name, name_token)

            offset_addr, type = self.expression()

            if not self.match(Tokens.SYMBOL, ']'):
                raise ParseError("expected closing ']'")

        return (name, self.get_symbol(name).addr, offset_addr, self.get_symbol(name).type)

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

        """
        Expressions
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
        Name
        """
        if self.match(Tokens.IDENTIFIER):
            return self.name(negate)

        """
        Numbers
        """
        if self.match(Tokens.INTEGER):
            addr = self.gen.set_new_reg(self.matched_token.value)
            if negate:
                addr = self.gen.set_new_reg("-1 * R[%d]" % addr)
            return (addr, self.matched_token.type)

        if self.match(Tokens.FLOAT):
            if negate:
                self.gen.write("tmp_float = -1 * %s;" % self.matched_token.value)
            else:
                self.gen.write("tmp_float = %s;" % self.matched_token.value)
            r = self.gen.new_reg()
            self.gen.write("memcpy(&R[%s], &tmp_float, sizeof(float));" % r)
            return (r, self.matched_token.type)


        """
        String
        """
        if self.match(Tokens.STRING):
            symbol = Symbol(self.matched_token.value, self.matched_token.type, len(self.matched_token.value)+1)
            symbol.isarray = True
            self.add_symbol(symbol)

            for i,c in enumerate(self.matched_token.value):
                self.gen.write("M[FP+%s] = '%s';" % (symbol.addr+i,c))

            self.gen.write("M[FP+%s] = '\\0';" % (symbol.addr+i+1))

            self.gen.write("SP = SP + %d;" % symbol.size)

            r = self.gen.set_new_reg("FP + %s" % symbol.addr)

            return (r, self.matched_token.type)

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

    def name(self, negate):
        """
        <name> ::= <identifier>[[<expression>]]
        """

        name = self.matched_token.value

        if name not in self.cur_symbols():
            raise ParseError("undefined identifier", token=self.prev_token)

        # if we already have this symbol in a register we dont need to asssign a new register
        """
        if self.get_symbol(name).current_reg:
            return (self.get_symbol(name).current_reg, self.get_symbol(name).type)
        """

        if not self.get_symbol(name).used:
            # TODO: if it is a global variable and we are currently
            # processing a procedure than this false triggers. Maybe
            # only check for non-global variables?
            self.warning("variable '%s' is uninitialized when used here" % name, token=self.prev_token)

        offset_reg = None

        if self.match(Tokens.SYMBOL, '['):

            if not self.get_symbol(name).isarray:
                raise ParseError("'%s' is not an array" % name, name_token)

            self.gen.comment("getting array '%s' offset" % name)
            offset_reg, type = self.expression()

            if not self.match(Tokens.SYMBOL, ']'):
                raise ParseError("expected closing ']'")
        elif self.get_symbol(name).isarray:
            return (None, None)

        if self.get_symbol(name).isglobal:
            if offset_reg:
                addr = self.gen.set_new_reg("M[%d+R[%s]]" % (self.get_symbol(name).addr, offset_reg))
            else:
                addr = self.gen.set_new_reg("M[%d]" % self.get_symbol(name).addr)
        else:
            if offset_reg:
                if self.get_symbol(name).indirect:
                    addr = self.gen.set_new_reg("M[M[FP+%d]+R[%s]]" % (self.get_symbol(name).addr, offset_reg))
                else:
                    addr = self.gen.set_new_reg("M[FP+%d+R[%s]]" % (self.get_symbol(name).addr, offset_reg))
            else:
                addr = self.gen.set_new_reg("M[FP+%d]" % self.get_symbol(name).addr)

        if negate:
            addr = self.gen.set_new_reg("-1 * R[%d]" % addr)

        # keep track of what register contains this symbols value
        self.get_symbol(name).current_reg = addr

        return (addr, self.get_symbol(name).type)


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
    print "Global Procedures"
    print "-"*50
    for x in parser.global_symbols:
        if not parser.global_symbols[x].type == 'procedure': continue
        print parser.global_symbols[x]

    print ""
    print "Global Symbols"
    print "-"*50
    for x in parser.global_symbols:
        if parser.global_symbols[x].type == 'procedure': continue
        print parser.global_symbols[x]

    print ""
    print "Program:"
    print "-"*50
    for line in gen.lines:
        print line

    gen.write_file("out.c")
