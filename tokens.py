class Tokens:

    symbols = [
        ':', ';', ',',
        '+', '-', '*', '/',
        '(', ')', '{', '}', '[', ']',
        '<', '<=', '>', '>=',
        '!=', '==', ':=',
        '&', '|',
    ]

    keywords = [
        'integer',
        'string',
        'int',
        'bool',
        'float',
        'global',
        'in',
        'out',
        'if',
        'then',
        'else',
        'is',
        'for',
        'not',
        'program',
        'procedure',
        'begin',
        'return',
        'end',
    ]

    # Token Types
    KEYWORD     = "KEYWORD"
    IDENTIFIER  = "IDENTIFIER"
    INTEGER     = "INTEGER"
    FLOAT       = "FLOAT"
    STRING      = "STRING"
    BOOL        = "BOOL"
    SYMBOL      = "SYMBOL"
    COMMENT     = "COMMENT"
    SPECIAL     = "SPECIAL"
    INVALID     = "INVALID"

    class Token(object):

        def __init__(self, scanner, _type=None, _value=""):

            self.filename = scanner.filename
            self.line_str = scanner.line.strip()
            self.line_num = scanner.line_num
            self.col_num = scanner.col_num
            self.value = _value
            self.type = _type

            # recalculate token column number ignoring beginning whitespace
            self.col_num -= len(scanner.line) - len(scanner.line.lstrip())

        def __repr__(self):
            return "<%s,%s>" % (self.type, self.value)
