from pymongo import MongoClient


class MongoUtils(object):
    """
    This class talks with mongo db.
    """

    def __init__(self, config):
        self.enable = config['mongo_db']['enable']
        self.connection_string = config['mongo_db']['connection_string']
        self.database_name = 'discord_binance'
        self.signal_collection = 'signals'
        self.db = None

    def get_db(self, database_name):
        """
        Gets db instance
        it will instantiate the client for the first call
        then it will get it from self object.
        """
        if not self.enable:
            return

        if self.db is not None:
            return self.db

        client = MongoClient(self.connection_string)
        db = client[database_name]
        self.db = db
        return db

    def insert_signals(self, doc):
        """
        Insert signal info into mongo db
        """
        if not self.enable:
            return

        db = self.get_db(self.database_name)
        collection = db[self.signal_collection]

        existing_doc = self.get_signal({"msg_id": doc['msg_id']})
        if existing_doc:
            return existing_doc

        inserted = collection.insert_one(doc)
        doc['_id'] = inserted.inserted_id
        return doc

    def get_signal(self, filter_obj):
        """
        Get signal info from mongo db
        """
        if not self.enable:
            return

        db = self.get_db(self.database_name)
        collection = db[self.signal_collection]

        return collection.find_one(filter_obj)

    def get_all_pending_buy_signals(self):
        """
        Get all open orders
        """
        if not self.enable:
            return

        db = self.get_db(self.database_name)
        collection = db[self.signal_collection]

        return collection.find({
            "bought": False
        })

    def update_signal(self, _id, update_doc):
        """
        Update a signal doc
        """
        if not self.enable:
            return

        db = self.get_db(self.database_name)
        collection = db[self.signal_collection]

        return collection.update({
            "_id": _id
        }, update_doc)
