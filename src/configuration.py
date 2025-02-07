
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://luca69892:SeitiRevio!@teste.pwufp.mongodb.net/?retryWrites=true&w=majority&appName=Teste"

client = MongoClient(uri, server_api=ServerApi('1'))

db = client.diario_db
collection = db["diario_data"]