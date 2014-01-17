class Tokens:

    symbols = [
        ':', ';', ',',
        '+', '-', '*', '/',
        '(', ')', '{', '}',
        '<', '<=', '>', '>=',
        '!=', '=', ':=',
    ]

    keywords = [
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
        'case',
        'for',
        'and',
        'or',
        'not',
        'program',
        'procedure',
        'begin',
        'return',
        'end',
    ]

    class Type():
        KEYWORD     = "KEYWORD"
        IDENTIFIER  = "IDENTIFIER"
        CONSTANT    = "CONSTANT"
        STRING      = "STRING"
        SYMBOL      = "SYMBOL"
        COMMENT     = "COMMENT"
        SPECIAL     = "SPECIAL"

    class Token(object):

        def __init__(self, _type=None, _value=""):
            self.filename = ""
            self.line_str = ""
            self.line_num = 0
            self.line_col = 0
            self.value = _value
            self.type = _type

        def __repr__(self):
            return "<%s,%s>" % (self.type, self.value)
