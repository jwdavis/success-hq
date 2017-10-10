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

from google.appengine.ext import ndb

class User(ndb.Model):
    # user info
    first_name =    ndb.StringProperty()
    last_name =     ndb.StringProperty()
    email =         ndb.StringProperty()

    # company info
    company =  ndb.StringProperty()

    # last event dates
    reg_date =      ndb.DateTimeProperty()
    last_use =      ndb.DateTimeProperty()
    last_call =     ndb.DateTimeProperty()
    last_comment =  ndb.DateTimeProperty()
    last_dialin =   ndb.DateTimeProperty()
    last_ticket =   ndb.DateTimeProperty()

    # total event counts
    num_uses =      ndb.IntegerProperty()
    num_calls =     ndb.IntegerProperty()
    num_ratings =   ndb.IntegerProperty()
    num_comments =  ndb.IntegerProperty()
    num_dialins =   ndb.IntegerProperty()
    num_tickets =   ndb.IntegerProperty()

    # misc 
    avg_rating =    ndb.FloatProperty()
    last_call_len = ndb.IntegerProperty()

class Company(ndb.Model):
    reg_date =      ndb.DateTimeProperty()
    boxes_bought =  ndb.IntegerProperty()
    boxes_prov =    ndb.IntegerProperty()

class Project(ndb.Model):
    company =       ndb.StringProperty()
    due =           ndb.DateTimeProperty()
    progress =      ndb.IntegerProperty()
    health =        ndb.IntegerProperty()
    name =          ndb.StringProperty()

class Renewal(ndb.Model):
    company =       ndb.StringProperty()
    due =           ndb.DateTimeProperty()
    amount =        ndb.IntegerProperty()
    health =        ndb.IntegerProperty()

class Trend(ndb.Model):
    company =       ndb.StringProperty()
    metric =        ndb.StringProperty()
    delta =         ndb.IntegerProperty()
    date =          ndb.DateTimeProperty()

