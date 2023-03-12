import os
import logging
import pymongo

MONGO_URI = os.getenv("INMETBOT_MONGO_URI")


modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)

class BotDatabase:
    """
    The BotDatabase object facilitates connection to the database.

    Attributes
    ----------
    client : MongoClient
        A MongoClient instance.
    db : Database
        the INMETBot database.
    alertsCollection : Collection
        the Alerts collection.
    subscribedChatsCollection : Collection
        the SubscribedChats collection.
    """

    def __init__(self):
        try:
            if not MONGO_URI:
                raise pymongo.errors.ConfigurationError(
                    f"Connection string is {MONGO_URI}"
                )
            # throw ServerSelectionTimeoutError if serverTimeout is exceeded
            serverTimeout = 20000
            self.client = pymongo.MongoClient(
                MONGO_URI, serverSelectionTimeoutMS=serverTimeout
            )
            self.client.server_info()
            modelsLogger.info("Connected to the INMETBot database!")

            self.db = self.client.INMETBot
            self.alertsCollection = self.db.Alerts
            self.subscribedChatsCollection = self.db.SubscribedChats
        except pymongo.errors.ServerSelectionTimeoutError as mongoClientErr:
            modelsLogger.error(
                f"Failed to connect to the INMETBot database: {mongoClientErr}"
            )
            exit(-1)
        except pymongo.errors.ConfigurationError as mongoClientErr:
            modelsLogger.error(
                f"Failed to connect to the INMETBot database: {mongoClientErr}"
            )
            exit(-1)


INMETBotDB = BotDatabase()
