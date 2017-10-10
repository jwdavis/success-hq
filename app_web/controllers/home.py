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

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from datetime import datetime
from datetime import timedelta

from datastore.models import Project, Renewal, Trend

class show(utils.BaseHandler):
    def get(self):
    	projects = Project.query().order(Project.due).fetch(3)
    	project_list = []
    	for project in projects:
    		logging.info(project.key.id())
    		project_list.append({"company":project.company, "name": project.name, "due": project.due.date(), "id": project.key.id()})


    	renewals = Renewal.query().order(Renewal.due).fetch(3)
    	renewal_list = []
    	for renewal in renewals:
    		renewal_list.append({"company":renewal.company, "amount": '${:,.2f}'.format(renewal.amount), "due": renewal.due.date(), "id": renewal.key.id(), "health": project.health})

    	trends = Trend.query().order(-Trend.date).fetch(3)
    	trend_list = []
    	for trend in trends:
    		trend_list.append({"company":trend.company, "metric": trend.metric, "change": trend.delta, "id": trend.key.id(), "date": trend.date.date()})

    	self.context['projects'] = project_list
    	self.context['renewals'] = renewal_list
    	self.context['trends'] = trend_list
        self.render('home.html')