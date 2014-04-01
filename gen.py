class Gen:

    def __init__(self, filename):

        self.filename = filename
        self.lines = []
        self.registers = []
        self.memory = []
        self.current_reg = 1
        self.current_mem = 0
        self.label_counts = {}

    def write(self, string):
        self.lines.append(string)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            f.write('#include "runtime.h"\n')
            f.write('int main(void) {\n')
            f.write('goto main;\n\n')
            f.write(open("runtime_inline.c").read())
            f.write('\n')
            f.writelines('\n'.join(self.lines))
            f.write("\n;\n") # put semicolon at the end in case the last thing we write is a label
            f.write("}\n")

    def set_new_reg(self, string):

        i = self.current_reg
        self.write("R[%d] = %s;" % (i, string))
        self.current_reg += 1
        return i

    def add_mem(self, string):

        i = self.current_mem
        self.lines.append("M[%d] = %s;" % (i, string))
        self.current_mem += 1
        return i

    def put_label(self, name):
        self.lines.append("%s:" % name)

    def new_label(self, prefix='label'):
        if prefix not in self.label_counts:
            self.label_counts[prefix] = 1
        i = self.label_counts[prefix]
        self.label_counts[prefix] += 1
        return "%s_%d" % (prefix, i)

    def goto_label(self, label):
        self.lines.append("goto %s;" % label)

    def push_stack(self, register):
        self.write("M[SP] = R[%s];" % register)
        self.write("SP--;")

    def pop_stack(self):
        reg = self.set_new_reg("M[SP]")
        self.write("SP++;")
        return reg
