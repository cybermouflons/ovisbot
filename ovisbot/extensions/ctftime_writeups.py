#!/usr/bin/env python

import re
import sys
import json
import requests

from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# write machinery to find `eventID` according to the CTF
URL = 'https://ctftime.org/event/{EVENT_ID}/tasks/'
HEADERS = {
    'User-Agent':'Mozilla/5.0'
}


# ----- [ Class Event ] ----- # BEGIN #
class Event():
    '''
    Event class
        name : str        
        id : int
        ctf_id : int
        ctftime_url : str
        e_url : str
        e_title : str
    '''
    def __init__(self, 
                e_name : str = '', 
                e_id : int = 0,
                e_ctf_id : int = 0,
                e_ctftime_url : str = '',
                e_url : str = '',
                e_title : str = ''
                ):
        self.e_name = e_name

        ''' @raises ValueError '''
        self.e_id = int ( e_id )
        self.e_ctf_id = int( e_ctf_id )
            
        self.e_ctftime_url = e_ctftime_url
        self.e_url = e_url
        self.e_title = e_title
        self.writeups = self.find_event_writeups

    # parse to dictionary
    def __dict__(self):
        e_dict = dict ({
            "name" : self.e_name,
             "id" : str(self.e_id),
             "ctf_id" : str(self.e_ctf_id),
             "ctftime_url" : str(self.e_ctftime_url),
             "url" : str(self.e_url),
             "title" : str(self.e_title)
        })
        return e_dict

    # return as string
    def __str__(self):
        return '\n'.join([
            f'Name: {self.e_name}',
            f'Event ID: {self.e_id}',
            f'CTF ID: {self.e_ctf_id}',
            f'URL: {self.e_url}',
        ])

    '''
    find event writeups:
        + find_by_name  => only this is supported now
        + find_by_id    => not implemented
        + find_by_url   => not implemented
    '''
    def find_event_writeups(self):
        url = 'https://ctftime.org/event/list/past'
        r = requests.get(url=url, headers=HEADERS)
        soup = BeautifulSoup(r.text, 'html.parser')

        # find Event by name
        found = False
        for i in soup.body.table.find_all('tr')[1::]:
            name = i.td.text
            e_name = self.e_name.split('.')[0]
            if e_name.upper() in name.upper():
                found = True
                href = i.a.get('href')
                start_ix, end_ix = re.search(r'\d+', href).span()
                self.e_id = int( href[start_ix:end_ix] )
                self.e_name = name
                break
        if not found:
            raise ValueError('Event not found')

        url = f'https://ctftime.org/event/{ str(self.e_id) }/tasks/'
        r = requests.get(url=url, headers=HEADERS)
        soup = BeautifulSoup(r.text, 'html.parser')

        writeups = []
        # for each entry
        for i in soup.find_all('tr')[1:]:
            url = i.a.get("href")
            name = i.a.get_text()

            try:
                tags = list(map(lambda x: x.get_text(), i.find_all('span')))
            except:
                tags = []
            
            all_td = i.find_all('td')
            points = all_td[1].get_text()
            no_writeups = all_td[-2].get_text()

            writeup = Writeup(name=name, 
                    points=points,
                    tags=tags,
                    no_writeups=no_writeups,
                    url=url)
            writeups.append( writeup )
        self.writeups = writeups
        return event.e_name, self.writeups
        
# ----- [ Class Event ] ----- # END #



# ----- [ Class Writeup ] ----- # BEGIN #
'''
Writeup Class
    name : str
    points : int
    tags : list
    no_writeups : int
    url : str
'''
class Writeup():
    def __init__(self, name : str = '',
                points : int = 0,
                tags : List[str] = [],
                no_writeups : int = 0,
                url : str = ''):
        self.name = name
        self.points = points
        self.tags = tags
        self.no_writeups = no_writeups
        self.url = url

    # parse as dictionary
    def __dict__(self):
        w_dict = dict ({
            "name:" : str( self.name ),
            "points" : int( self.points ),
            "tags" : list( self.tags ),
            "no_writeups" : int( self.no_writeups ),
            "url" : str( self.url )
        })
        return w_dict

    # return as string
    def __str__(self):
        return '\n'.join([
               f'Name: {self.name} ({self.points} pts)',
               f'Tags: {self.tags}',
               f'#Writeups: {self.no_writeups}',
               f'Writeup URL: https://ctftime.org{self.url}',
            ])
# ----- [ Class Writeup ] ----- # END #


# ----- [ Main ] -----
if __name__ == '__main__':
    
    if len(sys.argv) == 2:
        e_name = str( sys.argv[1] )
        event = Event (
            e_name = e_name,
            # e_id = 0,
            # e_ctf_id = 0,
            # e_ctftime_url = '',
            # e_url = '',
            # e_title = ''
        )

        ctf_name, writeups = event.find_event_writeups()
        n = len(ctf_name)
        print('=' * n, ctf_name, '=' * n, sep='\n')
        print( '\n\n'.join( map( str, writeups )))
        sys.exit(0)
    
    print(f'Usage: {sys.argv[0]} <name>')
    sys.exit(1)
