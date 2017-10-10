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

import utils
import logging
import json

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from datetime import datetime
from datetime import timedelta

from datastore.models import Project, Renewal, Trend
from bq import bq

def handle_ajax(card,customer):

    # retrieve comments for this customer from last 7 days
    if card == 'comments':        
        results = bq.do_query('comments_last_week',['comment','user','date'],customer)
        comments = []
        for row in results:
            comments.append([row['comment'],row['user']])
        return comments

    # retrieve call type chart data for this customer from last 7 days
    if card == 'calls':
        results = bq.do_query('calls_by_type_last_week',['call_type','calls'],customer)
        calls_by_type = [['Type','Calls']]
        for row in results:
            calls_by_type.append([row['call_type'],row['calls']])

        results = bq.do_query('calls_by_size_last_week',['call_num_users','calls'],customer)
        calls_by_users = [['# Users','Calls']]
        for row in results:
            calls_by_users.append([str(row['call_num_users']),row['calls']])

        results = bq.do_query('calls_by_os_last_week',['call_os','calls'],customer)
        calls_by_os = [['OS','Calls']]
        for row in results:
            logging.info(row)
            calls_by_os.append([row['call_os'],row['calls']])

        return {'cbt':calls_by_type,'cbu':calls_by_users,'cbo':calls_by_os}
    
    # get chart data for total provisioned boxes, last 30 days 
    if card == 'pct_provisioned_rolling':
        results = bq.do_query(card,['day','pct_provisioned'],customer)
        history = [['Date','% Provisioned']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['pct_provisioned']])
        if len(results) > 1:
            value = row['pct_provisioned']
        else:
            value = '--'

    # get chart data for this customer, registered user totals for last 30 days
    if card == 'reg_users_rolling':
        results = bq.do_query(card,['day','reg'],customer)
        history = [['Date','Reg. Users']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['reg']])
        if len(results) > 1:
            value = row['reg']
        else:
            value = '--'
        logging.info(history)

    if card == 'purchased_boxes_rolling':
        results = bq.do_query(card,['day','purchased'],customer)
        logging.info(results)
        history = [['Date','Purchased']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['purchased']])
        if len(results) > 1:
            value = row['purchased']
        else:
            value = '--'

    if card == 'provisioned_boxes_rolling':
        results = bq.do_query(card,['day','provisioned'],customer)
        history = [['Date','Registered']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['provisioned']])
        if len(results) > 1:
            value = row['provisioned']
        else:
            value = '--'

    # get chart data for this customer, 30 days of calls in previous 7 days
    if card == 'calls_sliding_7':
        results = bq.do_query(card,['day','calls'],customer)
        history = [['Date','Calls']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['calls']])
        if len(results) > 1:
            value = row['calls']
        else:
            value = '--'

    if card == 'active_users_sliding_7':
        results = bq.do_query(card,['day','sdau'],customer)
        history = [['Date','7DAU']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['sdau']])
        if len(results) > 1:
            value = row['sdau']
        else:
            value = '--'

    if card == 'ratings_sliding_7':
        results = bq.do_query(card,['day','avg_rating','num_rating'],customer)
        history = [['Date','Avg. Rating']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['avg_rating']])
        if len(results) > 1:
            value = {'avg':row['avg_rating'],'num':row['num_rating']}
        else:
            value = {'avg':'--','num':'--'}

    if card == 'dialin_sliding_7':
        results = bq.do_query(card,['day','dialins'],customer)
        history = [['Date','Dialins']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['dialins']])
        if len(results) > 1:
            value = row['dialins']
        else:
            value = '--'

    if card == 'support_sliding_7':
        results = bq.do_query(card,['day','support_tickets'],customer)
        history = [['Date','Support Tickets']]
        for row in results:
            history.append([row['day'].strftime('%m-%d-%Y'),row['support_tickets']])
        if len(results) > 1:
            value = row['support_tickets']
        else:
            value = '--'

    return {'value': value, 'history': history}

class show(utils.BaseHandler):
    def get(self,customer):

        # proceed only if customer is specified
        if customer != '':

            # determine which card is loading
            card = self.request.get('card')

            # if not home, then spit out chart data for appropriate card
            if card != '':
                self.response.out.write(json.dumps(handle_ajax(card,customer)))
                return

            # grab the number of purchased boxes and calc acv
            results = bq.do_query('purchased',['purchased'],customer)         
            acv = 0 
            for row in results:
                self.context['purchased'] = row['purchased']
                self.context['acv'] = row['purchased'] * 2499

            # render the home page
            self.context['customer'] = customer
            self.render('customer.html')