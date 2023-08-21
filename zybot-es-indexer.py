
import json
from dagster import AssetIn, asset, Config
import os

from elasticsearch import Elasticsearch

    
@asset
def indexer():
    cloud_id = 'ebooks:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRlOTdhNGI0NzBlMmE0OWNmYjBlMTBjOWJiMzQ2NTQxNSQ4OTQ5NjU2OTU3ZGM0MzUwOTYwYWU5ODcyZjEzMTVlZg=='  # Replace with your Elastic Cloud ID
    cloud_auth = ('elastic', 'n26ugDzFh4NhGldmQDKMyKm0')  # Replace with your Cloud username and password
    es = Elasticsearch( cloud_id=cloud_id, http_auth=cloud_auth )
    index_name = 'amazon'
    doc_type = "_doc"

    # Path to the JSON file
    json_file_path = "/Users/skaruppaiah1/projects/dagster-data-flows/input/amazon.books.json"


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



