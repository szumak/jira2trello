#!/usr/bin/env python3

import requests
# https://pypi.org/project/jira/
from jira import JIRA
import sys
import re
import json
from pprint import pprint

###
credentials_file = "config.ini"


with open(credentials_file, 'r') as f:
    config = json.load(f)

options = {'server': config['jira']['server']}

jira = JIRA(options,basic_auth=(config['jira']['user'], config['jira']['password']))

def add_trello_card( jira_issue, name ):
    trello_url = config['trello']['url'] + "cards"
    # We are going to add JIRA ticket url into the Trello note description
    description =  config['jira']['server'] + "/browse/" + jira_issue
    query = {
       'key':      config['trello']['key'],
       'token':    config['trello']['token'],
       'idList':   config['trello']['idList'],
       'idLabels': config['trello']['idLabels'],
       'name':     name,
       'desc':     description
    }
    response = requests.request(
       "POST",
       trello_url,
       params=query
    )
    #print(response.text)

def move_trello_card( card_id, list_id ):
    print("Moving %s to %s" % (card_id,list_id))
 
    trello_url = config['trello']['url'] + "cards/" + card_id

    query = {
       'key':      config['trello']['key'],
       'token':    config['trello']['token'],
       'idList':   list_id
    }
    response = requests.request(
       "PUT",
       trello_url,
       params=query
    )
    #print(response.text)

def add_fast_card( name, description ):
    trello_url = config['trello']['url']
    query = {
       'key':      config['trello']['key'],
       'token':    config['trello']['token'],
       'idList':   config['trello']['idList'],
       'idLabels': config['trello']['idLabels'],
       'name':     name,
       'desc':     description
    }
    response = requests.request(
       "POST",
       trello_url,
       params=query
    )

def get_jira_issues():
    issues = jira.search_issues('status in (Open, "In Progress", Reopened, "Waiting for support", "Waiting for customer", "Awaiting approval", Approved, "To Do", "AUTO - START", "On Hold") AND assignee in (currentUser())')
    return issues

def get_trello_cards():
    trello_url = config['trello']['url'] + "boards/{}/cards".format( config['trello']['board_id'] )
    query = {
       'key':      config['trello']['key'],
       'token':    config['trello']['token']
    }
    response = requests.request(
       "GET",
       trello_url,
       params=query
    )
    return json.loads(response.text)

#
#  START
#

if (len( sys.argv )  > 1) :
    subject = "[fast] " + sys.argv[1]
    #print("description:", flush=True)
    description=""
    for line in sys.stdin:
        if line == ".\n":
           break
        description = description + line
    add_fast_card( subject, description )

cards_names = {}
for card in get_trello_cards():
    cards_names[str(card['name'])] = card

    #print("Name: %s %s" % (card['name'],card['id']))


issues_list = get_jira_issues()
for issue in issues_list:
    #print('adding {}'.format(issue.key) )
    #print(issue.fields.status)
    move_to=config['trello']['status_mapping'][str(issue.fields.status)]

    res=0

    for key in cards_names:
        if issue.key in key:
            res=1
            if cards_names[key]['idList'] != move_to:
                move_trello_card(cards_names[key]['id'],move_to)

    if res == 0:
        print("adding card for {} - {}".format(issue.key, issue.fields.summary))
        add_trello_card( issue.key, '{}: {}'.format(issue.key, issue.fields.summary) )



for card in cards_names:
    sys_ticket=card.split(':')[0]
    move_to=config['trello']['status_mapping']['Closed']
    if re.match("[A-Z]+(?!-?[a-zA-Z]{1,10})", sys_ticket):
        res=0
        for issue in issues_list:
            if sys_ticket == issue.key:
                res=1
        if res == 0:
            if cards_names[card]['idList'] != move_to:
                    move_trello_card(cards_names[card]['id'],move_to)
        