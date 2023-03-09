
import os
from pymongo import MongoClient, WriteConcern
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pymongo
import requests
import re
import json
import threading
load_dotenv()
MONGOURI = os.environ.get("MONGOURI")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL")) or 600
if(not MONGOURI):
    raise Exception("MONGOURI Missing")

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t
def get_db():
    client = MongoClient(MONGOURI)
    return client['UREC_OCCUPANCY']


def is_open(tag):
    return tag.select_one('span[style*="color:#B30000"],span[style*="color:green"]').text == "(Open)"


def extract():
    # db = get_db()
    # collection = db['occupancies']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    res = requests.get(
        "https://connect2concepts.com/connect2/?type=bar&key=1a0b4030-78cb-4f32-90e5-3a041ac6b640", headers=headers)
    parsed = BeautifulSoup(res.text, features="lxml")
    bar_charts = parsed.select(".barChart")
    open_places = list(filter(is_open, bar_charts))
    return open_places

    # print(parsed_objs)


def transform(open_places):
    parsed_objs = [
        {
            "lastUpdated": re.search("Updated:\s(.*)", b.contents[-3]).group(1).strip(),
            "areaName":b.contents[0].strip(),
            "count":int(re.search("Last\sCount:\s(.*)", b.contents[4]).group(1).strip()),
            "percent":int(re.search("(.*)%", b.select_one(".barChart__row > .barChart__value").text).group(1).strip())

        } for b in open_places
    ]
    return parsed_objs


def load(docs):
    print(docs)
    collection = get_db()["occupancies"]
    try:
        collection.insert_many(docs,ordered=False)
    except pymongo.errors.BulkWriteError as e:
        pass


def main():

    open_places = extract()
    json_to_insert = transform(open_places)
    print(json.dumps(json_to_insert, indent=2))
    load(json_to_insert)
def start_thread():
    set_interval(main,5)


start_thread()