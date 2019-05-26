import os

from pymongo import MongoClient

client = MongoClient('mongo', username='root', password='example', port=27017)
serverdb = client['serverdb']