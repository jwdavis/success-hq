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

from google.cloud.proto.datastore.v1 import entity_pb2
from google.cloud.proto.datastore.v1 import query_pb2
from google.cloud import bigquery
from googledatastore import helper as datastore_helper, PropertyFilter

import apache_beam as beam
from apache_beam.io.gcp.datastore.v1.datastoreio import WriteToDatastore

from datetime import datetime
from datetime import timedelta
from datetime import date

from random import randint, uniform

import time
import sys
import os
import http

PROJECT=os.environ['DEVSHELL_PROJECT_ID']
DATASET='events'
TEMP = 'user_events_load'
BUCKET="{}-df".format(PROJECT)
USER_LIMIT = ""

good_comments = [u'Great!',u'Love this video thing!',u'Feels like I am there!', u'Good', u'Highfive rocks']
bad_comments = [u'Disconnected',u'Video dropouts',u'Crackling audio', u'Slows computer down', u'I am ugly']
oses = [u'Mac OSX', u'Windows', u'Linux', u'ios', u'Android']
call_types = ['Web', 'Presentation', 'Room-and-Web', 'Multi-room-and-Web']
drivers = [u'Video',u'Audio',u'Network']
project_list = [u'Pilot', u'Pro Eval', u'Global Launch', u'QBR', u'Case Study']
metric_list = [u'7DAU', u'CPW', u'CH/B/D', u'RU', u'Diversity']

# utility for showing contents of pcollections
def output(value):
  print value
  return value

# replace offset with reg_date and return row as dict
def get_user_with_regdate(row):
  new_row = dict(row)
  new_row['reg_date'] = datetime.now() + timedelta(days=-row['offset'],minutes=-randint(0,120))
  del new_row['offset']
  return new_row

# create tuple with company and registration date for each user
def get_company_and_regdate(row):
  return (row['company'],row['reg_date'])

# build the datastore entity for a user
def build_user_entity(row):
  entity = entity_pb2.Entity()
  datastore_helper.add_key_path(entity.key,'User',row['email'])
  props = dict(row)
  del props['email']
  datastore_helper.add_properties(entity,props)
  return entity

# build the datastore entity for a company
def build_company_entity(data):
  entity = entity_pb2.Entity()
  datastore_helper.add_key_path(entity.key,'Company',data[0])
  props = {}
  props['reg_date'] = data[1]
  props['boxes_bought'] = 0
  props['boxes_prov'] = 0
  datastore_helper.add_properties(entity,props)
  return entity

# create registration event tuple, with date and event data tuple
def build_reg_event(user):
  day = user['reg_date'].date()
  event = {}
  event['date']=user['reg_date'].strftime("%Y-%m-%d %H:%M:%S")
  event['type'] = 'register'
  event['user'] = user['email']
  event['company'] = user['company']
  return event

# create ticket event tuples, each with date and event data tuple
def build_ticket_events(user):
  seconds = (datetime.now() - user['reg_date']).total_seconds()
  days_since_reg = int(seconds / 86400)
  troubley = randint(0,3)
  tickets = int(days_since_reg / (4 - troubley) / 2) # change last for adjust ticket numbers

  for ticket in range(0,tickets):
    event_date = user['reg_date'] + timedelta(0,int(seconds/tickets/1.1) * ticket)

    event = {}
    event['date']= event_date.strftime("%Y-%m-%d %H:%M:%S")
    event['type'] = 'support_ticket'
    event['user'] = user['email']
    event['company'] = user['company']
    event['ticket_number'] = "{}-{}".format(event['user'],ticket)
    event['ticket_driver'] = drivers[randint(0,2)]

    day = event_date.date()
    yield event

def build_event_dict (**kwargs):
  cols = {}
  cols['date'] = None
  cols['type'] = None
  cols['user'] = None
  cols['company'] = None
  cols['call_duration'] = None
  cols['call_type'] = None
  cols['call_num_users'] = None
  cols['rating'] = None
  cols['comment'] = None
  cols['session_id'] = None
  cols['dialin_duration'] = None
  cols['ticket_number'] = None
  cols['ticket_driver'] = None
  cols['call_os'] = None

  cols.update(kwargs)
  return cols

# create list of call-related events
def build_call_events(user):
  os = oses[randint(0,4)]
  seconds = (datetime.now() - user['reg_date']).total_seconds()
  days_since_reg = int(seconds / 86400)
  freq = randint(1,10)

  calls = int (days_since_reg / (11-freq) * 10 ) # change last for adjust call numbers - default 4

  happy = randint(0,2)
  ratey = randint(0,2)
  commenty = randint(0,2)
  chatty = randint(0,4)
  seed = datetime(1980, 01, 01, 01, 00)

  call_num = 0

  for call in range(0,calls):
    event_list = []
    call_num += 1

    # figure out if caller was happy
    call_happy_score = randint(0,99)
    if call_happy_score >= (happy * 25):
        call_happy = True
    else:
        call_happy = False

    # figure out if they left rating, and  what it was
    call_rating_score = randint(0,99)
    if call_rating_score <= (ratey * 40):
        if call_happy:
            call_rating = randint(4,5)
        else:
            call_rating = randint(1,3)
    else:
        call_rating = None

    # figure out if they left a comment, and what it was
    call_comment_score = randint(0,99)
    if call_comment_score <= (commenty * 33 * ratey / 3):
        if call_rating >= 3:
            call_comment = good_comments[randint(0,4)]
        else:
            call_comment = bad_comments[randint(0,4)]
    else:
        call_comment = None

    # figure out how long the call was
    call_length = chatty * randint(5,20)

    # figure out if this was a dialin session
    call_dialin_score = randint(0,99)
    if call_dialin_score < 40:
        dialin_length = call_length
    else:
        dialin_length = None

    # figure out the type of call
    call_type_score = randint(0,99)
    if call_type_score < 35:
        call_type = call_types[0]
    elif call_type_score < 70:
        call_type = call_types[1]
    elif call_type_score < 90:
        call_type = call_types[2]
    else:
        call_type = call_types[3]

    # figure out the number of callers
    call_size_score = randint(0,99)
    if call_size_score < 35:
        call_users = 2
    elif call_size_score < 70:
        call_users = 3
    elif call_size_score < 95:
        call_users = 4
    else:
        call_users = (call_size_score - 90 + 5)

    # figure out call event date
    shift = int(seconds/calls+randint(-1000,1000)) * call_num
    event_date = user['reg_date'] + timedelta(0,shift)
    if event_date > datetime.now():
        event_date = datetime.now()
    day = event_date.date()
    session_id = str((datetime.now() - seed).total_seconds()) + '.' + str(call)

    event_list.append(build_event_dict(
      date = event_date.strftime("%Y-%m-%d %H:%M:%S"),
      type = 'call',
      user = user['email'],
      company = user['company'],
      call_duration = call_length,
      call_type = call_type,
      call_num_users = call_users,
      call_os = os,
      session_id = session_id
      ))

    event_list.append(build_event_dict(
      date = (event_date + timedelta(0,-60)).strftime("%Y-%m-%d %H:%M:%S"),
      type = 'load',
      user = user['email'],
      company = user['company']
      ))

    # rating events
    if call_rating:
      event_list.append(build_event_dict(
        date = event_date.strftime("%Y-%m-%d %H:%M:%S"),
        type = 'rating',
        user = user['email'],
        company = user['company'],
        rating = call_rating,
        session_id = session_id
        ))

    # Comment events
    if call_comment:
      event_list.append(build_event_dict(
        date = event_date.strftime("%Y-%m-%d %H:%M:%S"),
        type = 'comment',
        user = user['email'],
        company = user['company'],
        comment = call_comment,
        session_id = session_id
        ))

    # dialin events
    if dialin_length:
      event_list.append(build_event_dict(
        date = event_date.strftime("%Y-%m-%d %H:%M:%S"),
        type = 'dialin',
        user = user['email'],
        company = user['company'],
        call_duration = dialin_length
        ))

    yield event_list

def expand_events(events):
  for event in events:
    yield event

def build_company_events(company):
  event_list = []
  company_name = company[0]
  initial_purchase = randint(1,15)
  pur_event = {}
  pur_event['date'] = time.mktime(company[1].timetuple())
  pur_event['type'] = 'purchased'
  pur_event['company'] = company_name
  pur_event['purchased'] = initial_purchase
  event_list.append(pur_event)

  prov_date = company[1] + timedelta(randint(2,14)) #tweak depending on overall window 2/14
  initial_prov = randint(1,initial_purchase)
  for device in range(0,initial_prov):
    prov_event = {}
    prov_event['date'] = time.mktime(prov_date.timetuple())
    prov_event['type'] = 'provisioned'
    prov_event['company'] = company_name
    prov_event['purchased'] = None
    prov_event['provisioned'] = 1
    prov_event['serial_number'] = "A{}".format(randint(100000,2000000))
    prov_event['box_name'] = "{}.room.0{}".format(company_name, device+1)
    event_list.append(prov_event)

  seconds = (datetime.now() - company[1]).total_seconds()
  days_since_reg = int(seconds / 86400)
  months_since_reg = int(days_since_reg/30) + 1

  boxes = device + 1
  last_purchase_date = company[1]
  purchases = int(randint(1,2) * months_since_reg)
  for purchase in range(1, purchases):
      purchased = randint(5,15)
      upsell_period =  months_since_reg / (purchases + 1) * 14
      last_purchase_date = last_purchase_date + timedelta(upsell_period)
      pur_event = {}
      pur_event['date'] = time.mktime(last_purchase_date.timetuple())
      pur_event['type'] = 'purchased'
      pur_event['company'] = company_name
      pur_event['purchased'] = purchased
      event_list.append(pur_event)

      prov_date = last_purchase_date + timedelta(randint(2,14)) #tweak depending on overall window 2/14
      last_prov = randint(purchased//2,purchased)
      for device in range(1,last_prov+1):
          boxes += 1
          prov_event['date'] = time.mktime(prov_date.timetuple())
          prov_event['type'] = 'provisioned'
          prov_event['company'] = company_name
          prov_event['purchased'] = None
          prov_event['provisioned'] = 1
          prov_event['serial_number'] = "A{}".format(randint(100000,2000000))
          prov_event['box_name'] = "{}.room.0{}".format(company_name, boxes)
          event_list.append(prov_event)

  yield event_list

def build_project_entities(company):
  project = project_list[randint(0,4)]
  health_index = randint(0,5)
  if health_index < 1:
      health = randint(30,50)
  elif health_index < 2:
      health = randint (50,70)
  else:
      health = randint (70,100)
  progress = randint(50,95)
  entity = entity_pb2.Entity()
  datastore_helper.add_key_path(entity.key,'Project','{}-{}'.format(company[0],project))
  props = {}
  props['due'] = datetime.now()+timedelta(randint(30,60))
  props['name'] = project
  props['health'] = health
  props['progress'] = progress
  props['company'] = company[0]
  datastore_helper.add_properties(entity,props)
  return entity

def build_trending_entities(company):
  metric = metric_list[randint(0,4)]
  if randint(1,3) > 2:
      delta = randint(15,30)
  else:
      delta = -randint(15,30)

  entity = entity_pb2.Entity()
  datastore_helper.add_key_path(entity.key,'Trend','{}-{}'.format(company[0],metric))
  props = {}
  props['company'] = company[0]
  props['metric'] = metric
  props['delta'] = delta
  props['date'] = datetime.now()
  datastore_helper.add_properties(entity,props)
  return entity

def get_purchased_amounts(company_event):
  if company_event['type'] == 'purchased':
    output = (company_event['company'],company_event['purchased'])
    yield output

def get_provisioned_amounts(company_event):
  if company_event['type'] == 'provisioned':
    output = (company_event['company'],company_event['provisioned'])
    yield output

def build_renewal_entities(company_updates):

  # print company_updates
  amount = company_updates[1]['purchased'][0] * 2499

  health_index = randint(0,5)
  if health_index < 1:
      health = randint(10,30)
  elif health_index < 3:
      health = randint (30,60)
  else:
      health = randint (60,100)

  entity = entity_pb2.Entity()
  datastore_helper.add_key_path(entity.key,'Renewal','{}-{}'.format(company_updates[0],amount))
  props = {}
  props['due'] = datetime.now()+timedelta(randint(30,120))
  props['amount'] = amount
  props['health'] = health
  props['company'] = company_updates[0]
  datastore_helper.add_properties(entity,props)
  return entity

# main program
def run():
  argv = [
    '--project={0}'.format(PROJECT),
    '--job_name=shq-demo-data-{}'.format(datetime.now().strftime('%Y%m%d%H%M%S')),
    '--save_main_session',
    '--requirements_file=requirements.txt',
    '--staging_location=gs://{0}/staging/'.format(BUCKET),
    '--temp_location=gs://{0}/staging/'.format(BUCKET),
    '--runner=DataflowRunner'
  ]

  # create the pipeline
  p = beam.Pipeline(argv=argv)

  # get pcollection of users
  # read rows (dicts) from BQ
  # convert offset into actual date relative to today
  users = (p
    | 'read users from BQ' >> beam.io.Read(beam.io.BigQuerySource(query='SELECT * FROM [success-hq:datastore.user] order by email {}'.format(USER_LIMIT)))
    | 'get users with reg dates' >> beam.Map(get_user_with_regdate))

  # create list of companies and reg dates based on earliest user reg_date
  companies = (users
    | 'get company and reg date from user' >> beam.Map(get_company_and_regdate)
    | 'find first reg_date for company' >> beam.CombinePerKey(min)
    )

  # convert rows into datastore entities
  # write entities into datastore
  (users
    | 'build user entity' >> beam.Map (build_user_entity)
    | 'write user to Datastore' >> WriteToDatastore(PROJECT))

  # convert into datastore entities
  # write entities into datastore
  (companies
    | 'build company entity' >> beam.Map (build_company_entity)
    | 'write company to Datastore' >> WriteToDatastore(PROJECT))

  # create projects in datastore
  (companies
    | 'create project for company' >> beam.Map(build_project_entities)
    | 'write project to Datastore' >> WriteToDatastore(PROJECT))

  # create trending in datastore
  (companies
    | 'create trending for company' >> beam.Map(build_trending_entities)
    | 'write trending to Datastore' >> WriteToDatastore(PROJECT))

  # create events for company
  company_events = (
    companies
    | 'build company events' >> beam.FlatMap (build_company_events)
    | 'expand company events' >> beam.FlatMap (expand_events))

  # write company events into BQ
  (company_events
    | 'write to BQ table' >> beam.io.Write(beam.io.BigQuerySink(
      project = PROJECT,
      dataset = DATASET,
      table = 'company_events',
      write_disposition = beam.io.BigQueryDisposition.WRITE_TRUNCATE)))

  # find purchases for all companies
  purchases = (company_events
    | 'get purchased amounts' >> beam.FlatMap(get_purchased_amounts)
    | 'sum purchased amounts' >> beam.CombinePerKey(sum))

  # find provisions for all companies
  provisions = (company_events
    | 'get provisioned amounts' >> beam.FlatMap(get_provisioned_amounts)
    | 'sum provisioned amounts' >> beam.CombinePerKey(sum))

  # combine purchase and provision pcollections
  company_updates = {'purchased': purchases, 'provisioned': provisions} | beam.CoGroupByKey()

  # write renewal records to datastore
  (company_updates
    | 'create renewal for company' >> beam.Map(build_renewal_entities)
    | 'write renewals to Datastore' >> WriteToDatastore(PROJECT))

  # create registration events for users
  reg_events = users | 'build reg events' >> beam.Map(build_reg_event)

  # create tickets events for users
  ticket_events = users | 'build ticket events' >> beam.FlatMap(lambda line: build_ticket_events(line))

  # create call events for users
  call_events = (
    users
    | 'build call events' >> beam.FlatMap (build_call_events)
    | 'expand call events' >> beam.FlatMap (expand_events))

  # combine the pcollections
  events = (reg_events, ticket_events, call_events) | beam.Flatten()

  # take daily collections and write them into bq
  (events
    | 'write to bq' >> beam.io.Write(beam.io.BigQuerySink(
      '{}:{}.{}'.format(PROJECT,DATASET,TEMP),
      write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))
    )

  # run the pipeline
  print 'waiting for pipeline to finish, bq partition still to come'
  print 'do not close cloud shell window'
  status = p.run().wait_until_finish()

  # copy stuff from temp into partitions
  print 'starting bq partition work'
  today = date.today()
  days_past = 182
  bq_client = bigquery.Client(project=PROJECT)
  bq_dataset = bq_client.dataset(DATASET)
  for index in range(0,days_past):
    query_day = (datetime.now() + timedelta(days=1-index)).date()
    query_start = query_day.strftime('%Y-%m-%d 00:00:00')
    query_end = query_day.strftime('%Y-%m-%d 23:59:59')
    part_string = query_day.strftime('%Y%m%d')
    query = 'SELECT * FROM {}.{} where date >= "{}" and date <= "{}"'.format(DATASET,TEMP,query_start,query_end)
    bq_target = bq_dataset.table('user_events${}'.format(part_string))
    job = bq_client.run_async_query('bq_load_{}'.format(datetime.now().strftime('%Y%m%d%H%M%S%f')), query)
    job.destination = bq_target
    job.write_disposition = 'WRITE_TRUNCATE'
    job.begin()
  print 'Done! You can close the Cloud Shell window'

  # to do - delete temp table
  # user_event_temp_table = bq_dataset.table("user_events_load")
  # user_event_temp_table.delete()

if __name__ == '__main__':
   run()
