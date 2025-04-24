class Top:
    def __init__(self, filename):
        self.filename = filename
        self.size = 0
        self.things = []
        self.read()

    def add(self, thing, index):
        self.things.insert(index, thing)
        self.size = len(self.things)
        self.write()

    def read(self):
        with open(self.filename, 'r', encoding='utf-8') as file:
            self.things = [line.strip() for line in file if line.strip()]
            self.size = len(self.things)

    def write(self):
        with open(self.filename, 'w', encoding='utf-8') as file:
            file.write('\n'.join(self.things))
