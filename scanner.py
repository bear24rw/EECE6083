#! /usr/bin/env python
import sys
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

    def warning(self, message, column=None):

        if column is None:
            column = self.col_num

        print Color.BOLD + Color.WHITE + "%s:%s:%s: " % (self.filename, self.line_num, column) + Color.YELLOW + "warning: " + Color.WHITE + message
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

            self.line = line
            self.line_num += 1

            col_iter = self.col_iter()

            for char, next_char in col_iter:

                # if we see a space just skip it and keep looking
                if char in [' ', '\n']:
                    continue

                """
                Comments
                """
                if char == "/" and next_char == "/":

                    token = Tokens.Token()
                    token.type = Tokens.Type.COMMENT

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

                    token = Tokens.Token()
                    token.type = Tokens.Type.SYMBOL
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

                    token = Tokens.Token()
                    token.value += char

                    while next_char.isalnum() or next_char == '_':
                        token.value += next_char
                        char, next_char = next(col_iter)

                    if token.value in Tokens.keywords:
                        token.type = Tokens.Type.KEYWORD
                    else:
                        token.type = Tokens.Type.IDENTIFIER

                    yield token

                    continue

                """
                Constants
                """

                if char.isdigit():

                    token = Tokens.Token()
                    token.type = Tokens.Type.CONSTANT
                    token.value += char

                    while next_char.isdigit() or next_char == '.':
                        token.value += next_char
                        if token.value.count('.') == 2: break
                        char, next_char = next(col_iter)

                    if token.value.count('.') == 2:
                        self.warning("too many decimals", column=self.col_num+1)
                        break

                    if next_char.isalpha():
                        self.warning("expected constant but found '%s'" % next_char, column=self.col_num+1)
                        break

                    if next_char == '"':
                        self.warning("unexpected '\"' after constant", column=self.col_num+1)
                        break

                    yield token

                    continue

                """
                String Literal
                """

                if char == '"':

                    token = Tokens.Token()
                    token.type = Tokens.Type.STRING

                    while next_char != '"' and next_char != '\n':
                        token.value += next_char
                        char, next_char = next(col_iter)

                    # consume the trailing quotation mark
                    if next_char == '"':
                        next(col_iter)

                    if next_char == '\n':
                        self.warning("unexpected EOL while scanning string literal")
                        break

                    yield token

                    continue

                self.warning("Unsupported character")

        # return an EOF token since we are done
        yield Tokens.Token(Tokens.Type.SPECIAL, 'EOF')

if __name__ == "__main__":
    scanner = Scanner(sys.argv[1])
    for token in scanner.token_iter():
        print token
