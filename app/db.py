import json


class Collection:
    def __init__(self, parent, name, data):
        self.parent: Database = parent
        self.name: str = name
        self.data: list = data

    def save(self):
        self.parent.save()

    def find(self, rule: dict) -> dict:
        for doc in self.data:
            if all(doc[r] == rule[r] for r in rule):
                return doc

    def find_many(self, rule: dict) -> tuple:
        res = []
        for doc in self.data:
            if all(doc[r] == rule[r] for r in rule):
                res += [doc]
        return tuple(res)

    def insert_one(self, doc: dict):
        self.data += [doc]
        self.save()
        return doc

    def insert_many(self, docs: tuple):
        self.data += docs
        self.save()
        return docs

    def insert_if_unique(self, doc: dict):
        if doc not in self.data:
            self.data += [doc]
            self.save()
            return doc
        return None

    def delete(self, doc):
        try:
            self.data.remove(doc)
        except Exception as e:
            return None
        self.save()
        return doc

    def _delete(self, rule):
        d = self.find(rule)
        if d is None:
            return None
        self.data.remove(d)
        return d

    def update_field(self, rule, doc):
        d = self._delete(rule)
        if d is None:
            return None
        for k in doc:
            d[k] = doc[k]

        self.data += [d]
        self.save()
        return d

    def update(self, rule, new_doc):
        d = self._delete(rule)
        if d is None:
            return None
        self.data += new_doc
        self.save()
        return new_doc

    @property
    def json(self):
        return self.data


class Database:
    def __init__(self, filename: str):
        self.filename = filename
        d = self.data
        for collection in d:
            self.__setattr__(collection, Collection(self, collection, d[collection]))
        self.collections = d.keys()

    @property
    def data(self):
        return json.load(open(self.filename, mode='r'))

    @property
    def json(self):
        return {cname: self.__getattribute__(cname).json for cname in self.collections}

    def save(self) -> None:
        json.dump(self.json, open(self.filename, mode='w'))

    def __getitem__(self, item):
        try:
            return self.__getattribute__(item)
        except IndexError:
            raise IndexError(f'{item} not in collections list: {self.collections}')
