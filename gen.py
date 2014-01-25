class Gen:

    def __init__(self, filename):

        self.filename = filename
        self.lines = []
        self.registers = []
        self.memory = []
        self.current_reg = 0
        self.current_mem = 0
        self.current_label = 0

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

    def new_label(self):
        i = self.current_label
        self.current_label += 1
        return "label_%d" % i

    def goto_label(self, label):
        self.lines.append("goto %s" % label)
