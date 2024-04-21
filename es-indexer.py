import json
from dagster import AssetIn, asset, Config
import os
from dotenv import load_dotenv

from elasticsearch import Elasticsearch

load_dotenv()

ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")
ES_CLOUD_USERNAME=os.getenv("ES_CLOUD_USERNAME")
ES_CLOUD_PASSWORD=os.getenv("ES_CLOUD_PASSWORD")
ES_INDEX_NAME=os.getenv("ES_INDEX_NAME")

    
@asset
def indexer():
    cloud_id = ES_CLOUD_ID 
    cloud_auth = (ES_CLOUD_USERNAME, ES_CLOUD_PASSWORD) 
    es = Elasticsearch( cloud_id=cloud_id, http_auth=cloud_auth )
    index_name = 'amazon'
    doc_type = "_doc"

    # Path to the JSON file
    json_file_path = "input/amazon.books.json"


    # Read the JSON file
    with open(json_file_path, "r") as json_file:
        json_data = json.load(json_file)
    if isinstance(json_data, list):
        for document in json_data:
            if "_id" in document:
                document.pop("_id")
            # Index each eBook document
            es.index(index=index_name, body=document)

    # Refresh the index
    es.indices.refresh(index=index_name)
    print("Indexed {} documents".format(len(json_data)))
    return None



