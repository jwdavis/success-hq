# Copyright 2017 SuccessOps, LLC All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division

import webapp2
import utils
import logging
import json

from google.appengine.ext import ndb

from datetime import datetime
from datetime import timedelta

from datastore.models import User, Company
from bq import bq

def update_company(event_data):
    
    event_type = event_data['type']
    company = event_data['id']
    company_entity = ndb.Key(Company, company).get()

    if company_entity:
        if event_type == "purchased":
            purchased = company_entity.boxes_bought
            if not purchased:
                purchased = 0
            company_entity.boxes_bought = purchased+event_data['amount']

        if event_type == "provisioned":
            provisioned = company_entity.boxes_prov
            if not provisioned:
                provisioned = 0
            company_entity.boxes_prov = provisioned+1
    else:
        company_entity = Company(
            id=event_data['id'],
            reg_date=datetime.now()
        )
        company_entity.put()
        update_company(event_data)

    company_entity.put()


def update_user(event_data):

    count_properties = {
        "call": "num_calls",
        "load": "num_uses",
        "rating": "num_ratings",
        "comment": "num_comments",
        "support_ticket": "num_tickets",
        "dialin": "num_dialins"
    }

    count_last = {
        "call": "last_call",
        "load": "last_use",
        "comment": "last_comment",
        "support_ticket": "last_ticket",
        "dialin": "last_dialin"
    }

    # read user
    user = event_data['id']

    # create key
    user_entity = ndb.Key(User, user).get()
    event_type = event_data['type']

    if user_entity:

        # write passed values into user properties
        for key in event_data:
            if key in ['id', 'type']:
                pass
            else:
                setattr(user_entity, key, event_data[key])
        # update ratings average
        if event_type == 'rating':
            num_ratings = user_entity.num_ratings
            avg_rating = user_entity.avg_rating
            if not num_ratings:
                num_ratings = 0
            if not avg_rating:
                avg_rating = 0.0
            user_entity.avg_rating = ((avg_rating * num_ratings) + event_data['rating'])/(num_ratings+1)

        # increment counter on appropriate properties
        if event_type in count_properties:
            count = getattr(user_entity,count_properties[event_type])
            if not count:
                count = 0
            setattr(user_entity, count_properties[event_type], count+1)

        # update date/time on appropriate properties
        if event_type in count_last:
            setattr(user_entity, count_last[event_type], datetime.now())

    else:
        user_entity = User(
            id=event_data['id'],
            first_name=event_data['first_name'],
            last_name=event_data['last_name'],
            company=event_data['company'],
            reg_date=datetime.now()
            )
        user_entity.put()
        update_user(event_data)
    user_entity.put()

def update_bq(event_data):
    if "date" in event_data:
        event_date = datetime.strptime(event_data['date'], "%Y-%m-%d %H:%M%S") 
    else:
        event_date = datetime.now()
    if event_data['type'] == "purchased":
        row = [(event_date, event_data['type'], event_data['id'],event_data['amount'])]
        bq.add_event('company',row)
    elif event_data['type'] == "provisioned":
        row = [(event_date, event_data['type'],event_data['id'],None,1,event_data['serial_number'],event_data['device_name'])]
        bq.add_event('company',row)
    else:
        if event_data['type'] == "register":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'])]
        elif event_data['type'] == "load":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'])]
        elif event_data['type'] == "call":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'],event_data['last_call_len'],event_data['call_type'],event_data['num_users'],event_data['os'])]
        elif event_data['type'] == "rating":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'],None,None,None,None,event_data['rating'],None,event_data['session_id'])]
        elif event_data['type'] == "comment":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'],None,None,None,None,None,event_data['comment'],event_data['session_id'])]
        elif event_data['type'] == "dialin":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'],None,None,None,None,None,None,None,event_data['dialin_len'])]
        elif event_data['type'] == "support_ticket":
            row = [(event_date,event_data['type'],event_data['id'],event_data['company'],None,None,None,None,None,None,None,None,event_data['ticket_number'],event_data['driver'])]
        else:
            return
        bq.add_event('user',row)

class event_processor(utils.BaseHandler):
    def post(self):
    	event_data = json.loads(self.request.get('event_data'))
        if event_data['type'] in ["purchased","provisioned"]:
            update_company(event_data)
        else:
            update_user(event_data)
        update_bq(event_data)
    		
    	self.response.headers.add_header('Access-Control-Allow-Origin','*')
        self.response.out.write(json.dumps({'message':'Event recorded'}))

class syb(utils.BaseHandler):
    def get(self):
    	self.response.headers.add_header("Access-Control-Allow-Origin",'*')
        self.response.out.write('Welcome to api_events')

app = webapp2.WSGIApplication([
    ('/event/add',event_processor),
    (r'.*', syb)],
    debug=True)