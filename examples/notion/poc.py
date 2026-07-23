import logging
import os
from notion_client import Client,APIErrorCode, APIResponseError
from pprint import pprint

notion = Client(
    auth= os.environ["NOTION_TOKEN"],
    log_level=logging.DEBUG,
)

# List users
def users_list():
    list_users_response = notion.users.list()
    return (list_users_response)

# List Databases
def databases_list():
    list_databases = notion.databases.list()
    return(list_databases)

# Query a Database
def databases_query(database_id):
    list_databases_response = notion.databases.query(database_id)
    pprint(list_databases_response)

# Query a database which contains a string
def database_query_string(database_id,text):
    try:
        my_page = notion.databases.query(
            **{
                "database_id": f"{database_id}",
                "filter": {
                    "property": f"{text}",
                    "text": {
                        "contains": "found",
                    },
                },
            }
        )
        pprint(my_page)
    except APIResponseError as error:
        if error.code == APIErrorCode.ObjectNotFound:
            ...  # For example: handle by asking the user to select a different database
        else:
            # Other error handling code
            logging.exception('ERROR')

# Retrieve a page
def pages_retreive(page_id):
    page_content = notion.pages.retrieve(page_id)
    pprint(page_content)

    #retieve a property
    print(page_content['properties']['Difficulty']['multi_select'][0]['name'])

# Update a page
def pages_update(page_id,page_content):
    notion.pages.update(f"{page_id}",**page_content)

# Create a page
def pages_create(page_content):
    page = notion.pages.create(**page_content)
    return page['id']

# Create a new database inside a page
def databases_create(new_database):    
    db = notion.databases.create(**new_database)
    return db['id']

if __name__ == "__main__":
    #Search all databases enrolled
    databases = databases_list()
    for result in databases['results']:
        print('ID: '+ result['id']+' Title: '+ result['title'][0]['plain_text'])
    
    # Main Database:
    notion_database=os.environ["NOTION_DATABASE"]

    # Create a CTF Page
    ctf_name = "CyberMouflons CTF 2021"
    new_ctf={
    'parent': {
        'database_id': notion_database,
        'type': 'database_id'
    },
    'properties': {
                'Format': {
                    'id': '2921426f-bd1e-47d6-a50e-f102e1d38937',
                    'select': {
                        'name': 'jeopardy'},
                    'type': 'select'},
                'Name': {
                    'id': 'title',
                    'title': [{
                        'annotations': {
                            'bold': False,
                            'code': False,
                            'color': 'default',
                            'italic': False,
                            'strikethrough': False,
                            'underline': False},
                            'href': None,
                            'plain_text': f'{ctf_name}',
                            'text': {
                                'content': f'{ctf_name}',
                                'link': None},
                        'type': 'text'}],
                    'type': 'title'}}}
    page_id = pages_create(new_ctf) 

    # Create a database (table) under a CTF Page
    new_database={
    "parent": {
        "type": "page_id",
        "page_id": f"{page_id}"
    },
    "title": [
        {
            "type": "text",
            "text": {
                "content": "Challenges",
                "link": None
            }
        }
    ],
    "properties": {
        "Name": {
            "title": {}
        },
        "Description": {
            "rich_text": {}
        },
        "Category": {
            "select": [
                {
                    "name":"pwn",
                    "color":"red",
                },
                {
                    "name":"web",
                    "color":"green",
                }
            ]
        },
        "Difficulty": {
            "select": {
                "options": [
                    {
                        "name": "Easy",
                        "color": "green"
                    },
                    {
                        "name": "Medium",
                        "color": "orange"
                    },
                    {
                        "name": "Hard",
                        "color": "red"
                    }
                ]
            }
        },
        "Status": {
            "select": {
                "options": [
                    {
                        "name": "Null",
                        "color": "gray"
                    },
                    {
                        "name": "Ongoing",
                        "color": "green"
                    },
                    {
                        "name": "Solved",
                        "color": "red"
                    }
                ]
            }
        },
        "Active Team Member": {
            "type": "multi_select",
            "multi_select": {
                "options": [
                    {
                        "name": "s1kk1s",
                        "color": "blue"
                    },
                    {
                        "name": "rokos",
                        "color": "gray"
                    }
                ]
            }
        }
    }
}
    db = notion.databases.create(**new_database)
    db_id = databases_create(new_database)

    # Add a new challenge under the new CTF 
    challenge_page={
    'parent': {
        'database_id': db_id,
        'type': 'database_id'
    },
    'properties': {
                'Category': {
                    'id': '2921426f-bd1e-47d6-a50e-f102e1d38937',
                    'select': {
                        'name': 'Crypto'},
                    'type': 'select'},
                'Name': {
                    'id': 'title',
                    'title': [{
                        'annotations': {
                            'bold': False,
                            'code': False,
                            'color': 'default',
                            'italic': False,
                            'strikethrough': False,
                            'underline': False},
                            'href': None,
                            'plain_text': 'Testing',
                            'text': {
                                'content': 'Testing',
                                'link': None},
                        'type': 'text'}],
                    'type': 'title'}}}
    pages_create(challenge_page)

    # Other utilities:
    # pprint(users_list())
    # databases_query("5a4c9dba-6bc6-4dac-a67f-efd6d092f04a")
    # database_query_string("f6c7eb9b-ca48-45c9-90f0-0df025f389a2","Description")
    # pages_retreive("7f4d341d-c219-4446-954d-dd5082fed256")
    # pages_update("7f4d341d-c219-4446-954d-dd5082fed256",notion.pages.retrieve("7f4d341d-c219-4446-954d-dd5082fed256"))
