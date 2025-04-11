class Top:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename)
        self.read()
        self.size = len(self.things)

    def add(self, thing, index):
        self.things.insert(index, thing)
        open(self.filename, 'w').write('\n'.join(self.things))
        self.size += 1

    def read(self):
        self.things = self.file.read().strip().split('\n')

    def write(self):
        for thing in self.things:
            self.file.write(thing + '\n')
