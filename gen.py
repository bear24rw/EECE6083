class Gen:

    def __init__(self, filename):

        self.filename = filename
        self.lines = []
        self.registers = []
        self.memory = []
        self.current_reg = 0
        self.current_mem = 0
        self.label_counts = {}

    def set_new_reg(self, string):

        i = self.current_reg
        self.lines.append("R[%d] = %s" % (i, string))
        self.current_reg += 1
        return i

    def add_mem(self, string):

        i = self.current_mem
        self.lines.append("M[%d] = %s" % (i, string))
        self.current_mem += 1
        return i

    def write(self, string):
        self.lines.append(string)

    def put_label(self, name):
        self.lines.append("%s:" % name)

    def new_label(self, prefix='label'):
        if prefix not in self.label_counts:
            self.label_counts[prefix] = 1
        i = self.label_counts[prefix]
        self.label_counts[prefix] += 1
        return "%s_%d" % (prefix, i)

    def goto_label(self, label):
        self.lines.append("goto %s" % label)

    def push_stack(self, register):
        self.write("M[SP] = R[%s]" % register)
        self.write("SP++")
