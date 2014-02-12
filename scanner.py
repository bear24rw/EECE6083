#! /usr/bin/env python

from itertools import izip_longest
from color import Color
from tokens import Tokens

class Scanner:

    def __init__(self, filename):

        self.filename = filename

        self.f = open(filename)
        if not self.f:
            print "Could not open file!"
            sys.exit(1)

        self.line_num = 0
        self.col_num = 0
        self.has_errors = False

    def warning(self, message, column=None):

        self.print_message(message, "warning", column, Color.YELLOW)

    def error(self, message, column=None):

        self.has_errors = True
        self.print_message(message, "error", column, Color.RED)

    def print_message(self, message, label="info", column=None, color=Color.WHITE):

        if column is None:
            column = self.col_num

        column -= len(self.line) - len(self.line.lstrip())

        print Color.BOLD + Color.WHITE + "%s:%s:%s: " % (self.filename, self.line_num, column) + color + "%s: " % label + Color.WHITE + message
        print Color.DEFAULT + self.line.strip()
        print Color.GREEN + "%s^" % (' '*(column-1)) + Color.DEFAULT

    def col_iter(self):
        """
        Returns an iterator that produces the current and next character in the line
        Example: if the current line is "abc" the iterator will produce:
            ('a', 'b')
            ('b', 'c')
            ('c', None)
        It also keeps track of the current column number
        """
        self.col_num = 0
        for _ in izip_longest(self.line, self.line[1:]):
            self.col_num += 1
            yield _

    def token_iter(self):

        self.line_num = 0

        for line in self.f:

            line = line.lower()
            self.line = line
            self.line_num += 1

            col_iter = self.col_iter()

            for char, next_char in col_iter:

                # if we see a space just skip it and keep looking
                if char in [' ', '\t']:
                    continue

                # if its a newline insert a special token and then skip it
                if char == '\n':
                    yield Tokens.Token(self, Tokens.SPECIAL, '\n')
                    continue

                """
                Comments
                """
                if char == "/" and next_char == "/":

                    token = Tokens.Token(self)
                    token.type = Tokens.COMMENT

                    # consume until end of the line
                    while next_char:
                        token.value += char
                        char, next_char = next(col_iter)

                    yield token

                    continue

                """
                Symbols
                """

                if any(x.startswith(char) for x in Tokens.symbols):

                    token = Tokens.Token(self)
                    token.type = Tokens.SYMBOL
                    token.value = char

                    while any(x.startswith(token.value+next_char) for x in Tokens.symbols):
                        token.value += next_char
                        char, next_char = next(col_iter)

                    yield token

                    continue

                """
                Keywords and identifiers
                """

                if char.isalpha() or char == "_":

                    token = Tokens.Token(self)
                    token.value += char

                    while next_char.isalnum() or next_char == '_':
                        token.value += next_char
                        char, next_char = next(col_iter)

                    if next_char == '"':
                        self.error("unexpected '\"' after identifier", column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    if token.value in ['true', 'false']:
                        token.type = Tokens.BOOL
                    elif token.value in Tokens.keywords:
                        token.type = Tokens.KEYWORD
                    else:
                        token.type = Tokens.IDENTIFIER

                    yield token

                    continue

                """
                Numbers
                """

                if char.isdigit() or char == '.':

                    token = Tokens.Token(self)
                    token.type = Tokens.INTEGER
                    token.value += char

                    if char == '.':
                        self.warning("number should not start with decimal point, inserting leading '0'")
                        token.value = '0' + token.value

                    while next_char.isdigit() or next_char == '.':
                        token.value += next_char
                        if token.value.count('.') == 2: break
                        char, next_char = next(col_iter)

                    if token.value.count('.') == 2:
                        self.error("too many decimals", column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    if next_char.isalpha():
                        self.error("expected number but found '%s'" % next_char, column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    if next_char == '"':
                        self.error("unexpected '\"' after number", column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    if token.value.endswith('.'):
                        self.warning("number should not end with decimal point, inserting trailing '0'")
                        token.value += '0'

                    if '.' in token.value:
                        token.type = Tokens.FLOAT

                    yield token

                    continue

                """
                String Literal
                """

                if char == '"':

                    token = Tokens.Token(self)
                    token.type = Tokens.STRING

                    while next_char.isalnum() or next_char in " _,;:.'":
                        token.value += next_char
                        char, next_char = next(col_iter)

                    if next_char == '\n':
                        self.error("unexpected EOL while scanning string literal", column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    if not next_char == '"':
                        self.error("illegal string character '%s'" % next_char, column=self.col_num+1)
                        yield Tokens.Token(self, Tokens.INVALID)
                        break

                    # consume the trailing quotation mark
                    next(col_iter)

                    yield token

                    continue

                self.error("unsupported character '%s'" % char)

        # return an EOF token since we are done
        yield Tokens.Token(self, Tokens.SPECIAL, 'EOF')

if __name__ == "__main__":
    import sys
    scanner = Scanner(sys.argv[1])
    for token in scanner.token_iter():
        if token.value != '\n': print token
