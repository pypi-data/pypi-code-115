from PyFileCP import replacetool

class Copy:
    def __init__(self, inputfile, outputfile):
        self.input = open(inputfile, 'r')
        self.output = open(outputfile, 'w')
        self.content = self.input.read()
    def __enter__(self):
        def replacefunc(replacetext, replacewith):
            self.content = replacetool.replace(self.content, replacetext, replacewith)
        return replacefunc
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def commit(self):
        self.output.write(self.content)

