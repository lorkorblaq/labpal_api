from engine import db_clinical


collections = db_clinical.list_collection_names()
print(collections)

class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        
class Item:
    def __init__(self, name, category, in_stock, unit, per_pack, machine, bench):
        self.name = name
        self.category = category
        self.in_stock = in_stock
        self.unit = unit
        self.per_pack = per_pack
        self.machine = machine
        self.bench = bench

class channels:
    def __init__(self, name, channel, in_stock, unit, per_pack, machine, bench):
        self.name = name
        self.channel = channel
        self.in_stock = in_stock
        self.unit = unit
        self.per_pack = per_pack
        self.machine = machine
        self.bench = bench

class Put_in_use:
    def __init__(self, name, channel, in_stock, unit, per_pack, machine, bench):
        self.name = name
        self.channel = channel
        self.in_stock = in_stock
        self.unit = unit
        self.per_pack = per_pack
        self.machine = machine
        self.bench = bench
