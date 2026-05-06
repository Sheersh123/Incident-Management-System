from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class MongoClient:
    client: AsyncIOMotorClient = None

mongo_helper = MongoClient()

async def connect_to_mongo():
    mongo_helper.client = AsyncIOMotorClient(settings.MONGO_URL)

async def close_mongo_connection():
    if mongo_helper.client:
        mongo_helper.client.close()

def get_nosql_db():
    return mongo_helper.client.get_database()
