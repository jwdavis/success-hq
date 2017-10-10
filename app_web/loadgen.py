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
import json
import logging

from random import randint, uniform

from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from bq import bq
from datetime import datetime
from datetime import timedelta
import time

from datastore.models import User, Company, Trend, Renewal, Project

def make_sample_events(level):

    seed = datetime(1980, 01, 01, 01, 00)

    if level == 'low':
        loops = 2
        delay = 0.5
        limit = 1000
    elif level == 'med':
        loops = 4
        delay = 0.15
        limit = 10000
    else:
        loops = 20
        delay = 0.01
        limit = 1000000

    logging.info('loadgen info {},{},{}'.format(level,loops,delay))

    for index in range(1,loops):
        logging.info('in loop')

        q = User.query()
        for user in q.fetch(limit=limit):
            time.sleep(delay)
     
            # set some crap up
            good_comments = ["Great!","Love this video thing!","Feels like I am there!", "Good", "Highfive rocks"]
            bad_comments = ["Disconnected","Video dropouts","Crackling audio", "Slows computer down", "I am ugly"]
            call_types = ['Web', 'Presentation', 'Room-and-Web', 'Multi-room-and-Web']
            oses = ["Mac OSX", "Windows", "Linux", "ios", "Android"]
            call_length = randint(5,60)
            num_users = randint(2,8)
            os = oses[randint(0,4)]

            # build call-related events
            event_type = randint(1,10)
            if event_type < 5:

                event_data = {
                    "type":             "call",
                    "id":               user.key.id(),
                    "last_call_len":    call_length,
                    "call_type":        call_types[randint(0,3)],
                    "num_users":        num_users,
                    "os":               os,
                    "company":          user.company
                }
                taskqueue.add(url='/event/add',method='POST',target="api-events",params={"event_data":json.dumps(event_data)}) 

                event_data = {
                    "type":             "load",
                    "id":               user.key.id(),
                    "company":          user.company
                }
                taskqueue.add(url='/event/add',method='POST',target="api-events",params={"event_data":json.dumps(event_data)}) 

            elif event_type < 7:
            # rating events
                event_data = {
                    "type":             "rating",
                    "rating":           randint(3,5),
                    "session_id":       str((datetime.now() - seed).total_seconds()),
                    "id":               user.key.id(),
                    "company":          user.company
                }
                taskqueue.add(url='/event/add',method='POST',target="api-events",params={"event_data":json.dumps(event_data)})

            elif event_type == 8:
            # Comment events
                if randint(1,3) > 1:
                    call_comment = good_comments[randint(0,4)]
                else:
                    call_comment = bad_comments[randint(0,4)]
                event_data = {
                    "type":             "comment",
                    "comment":          call_comment,
                    "session_id":       str((datetime.now() - seed).total_seconds()),
                    "id":               user.key.id(),
                    "company":          user.company
                }
                taskqueue.add(url='/event/add',method='POST',target="api-events",params={"event_data":json.dumps(event_data)})

            else:
            # dialin events
                event_data = {
                    "type":             "dialin",
                    "dialin_len":       randint(5,60),
                    "id":               user.key.id(),
                    "company":          user.company
                }
                taskqueue.add(url='/event/add',method='POST',target="api-events",params={"event_data":json.dumps(event_data)})

class go(utils.BaseHandler):
    # @login_required
    def get(self):
        level = self.request.get('level')
        if level == '':
            level='low'
        q = self.request.get('q')
        if q == 'yes':
            taskqueue.add(url='/go_long',method='GET',params={"level":level})
        else:
            make_sample_events(level)

class go_long(utils.BaseHandler):
    # @login_required
    def get(self):
        level = self.request.get('level')
        if level == '':
            level='low'
        make_sample_events(level)

