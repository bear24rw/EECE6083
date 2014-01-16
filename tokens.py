class Tokens:

    arith_ops = ['=', '+', '-', '*', '/', '%']
    comp_ops = ['==', '!=', '<>', '>', '<', '>=', '<=']
    logic_ops = ['!', '&&', '||']
    brackets = ['(', ')', '[', ']', '{', '}']
    special = [',', ';']

    symbols = arith_ops + comp_ops + logic_ops + brackets + special

    keywords = [
            'if', 'endif',
            'while', 'endwhile',
            'int', 'double'
            ]

    class Type():
        KEYWORD     = "KEYWORD"
        IDENTIFIER  = "IDENTIFIER"
        CONSTANT    = "CONSTANT"
        STRING      = "STRING"
        SYMBOL      = "SYMBOL"
        OPERATOR    = "OPERATOR"
        SPECIAL     = "SPECIAL"
        UNKNOWN     = "UNKNOWN"
        COMMENT     = "COMMENT"

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