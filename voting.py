import json

class Voting:
    def __init__(self, top_size, voters_number):
        self.top_size = top_size
        self.voters_number = voters_number
        self.read()

    def __getitem__(self, key):
        return self.voting[key]

    def __setitem__(self, key, value):
        self.voting[key] = value

    def vote(self, user_id, option):
        self.read()
        if user_id not in self.voting['votes']:
            self.voting['votes'][user_id] = option
        self.write()

    def is_over(self):
        self.read()
        values = list(self.voting['votes'].values())
        return values.count(1) > self.voters_number // 2 or values.count(2) > self.voters_number // 2

    def result(self):
        return max((1, 2), key=list(self.voting['votes'].values()).count)

    def get_state(self):
        self.read()
        values = list(self.voting['votes'].values())
        result = self['new_thing'] + ' - ' + str(values.count(1)) + '\n'
        result += self['old_thing'] + ' - ' + str(values.count(2))
        return result

    def on(self):
        self.voting = {
            'is_active': True,
            'votes': {},
            'left': 0,
            'right': self.top_size,
            'cur_index': None,
            'new_thing': None,
            'old_thing': None
        }
        self.write()

    def off(self):
        self.voting = {
            'is_active': False,
            'votes': {},
            'left': 0,
            'right': self.top_size,
            'cur_index': None,
            'new_thing': None,
            'old_thing': None
        }
        self.write()

    def next_step(self, things):
        if self['left'] == len(things):
            self.voting['cur_index'] = len(things) - 1
            self.voting['old_thing'] = things[-1]
        else:
            self.voting['cur_index'] = (self.voting['left'] + self.voting['right']) // 2
            self.voting['old_thing'] = things[self['cur_index']]
        self.voting['votes'] = {}
        self.write()

    def get_vote_ask(self):
        result = '\nЧто лучше?\n\n'
        result += f"1. {self.voting['new_thing']}\n"
        result += f"2. {self.voting['old_thing']}"
        return result

    def read(self):
        with open('votings.json', 'r', encoding='UTF-8') as file:
            self.voting = json.load(file)

    def write(self):
        with open('votings.json', 'w', encoding='UTF-8') as file:
            json.dump(self.voting, file, ensure_ascii=False, indent=4)

    def is_on(self):
        self.read()
        return self.voting['is_active']

