class Gen:

    def __init__(self, filename):

        self.filename = filename
        self.lines = []
        self.registers = []
        self.memory = []
        self.current_reg = 1
        self.current_mem = 0
        self.label_counts = {}

    def write(self, string, indent='    '):
        self.lines.append(indent+string)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            f.write('#include "runtime.h"\n')
            f.write('int main(void) {\n')
            f.write('    goto main;\n\n')
            f.write(open("runtime_inline.c").read())
            f.write('\n')
            f.writelines('\n'.join(self.lines))
            f.write('\n\n')
            f.write("return 0;\n")
            f.write("}\n")

    def new_reg(self):
        i = self.current_reg
        self.current_reg += 1
        return i

    def set_new_reg(self, string):

        i = self.current_reg
        self.write("R[%d] = %s;" % (i, string))
        self.current_reg += 1
        return i

    def move_mem_to_reg(self, mem, reg):
        self.write("R[%s] = M[FP+%s];" % (reg, mem))

    def move_reg_to_mem_global(self, reg, mem):
        self.write("M[%s] = R[%s];" % (mem, reg))

    def move_reg_to_mem(self, reg, mem):
        self.write("M[FP+%s] = R[%s];" % (mem, reg))

    def move_reg_to_mem_indirect(self, reg, mem):
        self.write("M[R[%s]] = R[%s];" % (mem, reg))

    def comment(self, string):
        self.write("/* %s */" % string)
        #self.write('printf("%s\\n");' % string)

    def add_mem(self, string):

        i = self.current_mem
        self.lines.append("M[%d] = %s;" % (i, string))
        self.current_mem += 1
        return i

    def put_label(self, name):
        self.write("%s:" % name, indent='')

    def new_label(self, prefix='label'):
        if prefix not in self.label_counts:
            self.label_counts[prefix] = 1
        i = self.label_counts[prefix]
        self.label_counts[prefix] += 1
        return "%s_%d" % (prefix, i)

    def goto_label(self, label):
        self.write("goto %s;" % label)

    def push_stack(self, register):
        self.write("M[SP] = R[%s];" % register)
        self.write("SP++;")

    def pop_stack(self):
        reg = self.set_new_reg("M[SP]")
        self.write("SP--;")
        return reg

    def dec_sp(self, amount=1):
        self.write("SP = SP - %d;" % amount)

    def inc_sp(self, amount=1):
        self.write("SP = SP + %d;" % amount)

    def set_fp(self, addr):
        self.write("FP = %s;" % addr)

    def set_sp_to_fp(self):
        self.write("SP = FP;")

    def set_fp_to_sp(self):
        self.write("FP = SP;")

    def return_to_caller(self, params):
        self.comment("returning")

        self.comment("getting return address")
        return_reg = self.set_new_reg("M[FP-2];")

        self.comment("restore previous fp")
        self.write('printf("restoring FP: %d\\n", M[FP-1]);')
        self.set_fp("M[FP-1];")

        self.comment("restore previous sp")
        size = sum([s.size for s in params])
        self.write("SP = SP - %s;" % size)

        self.write("goto *(void *)R[%s];" % return_reg)

