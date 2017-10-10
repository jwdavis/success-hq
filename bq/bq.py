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

import logging
import uuid
import time
import queries

from google.cloud import bigquery
from datetime import datetime, timedelta

client = bigquery.Client()
dataset = client.dataset('events')
user_event_table = dataset.table("user_events")
user_event_temp_table = dataset.table("user_events_load")
company_event_table = dataset.table("company_events")

tables = {}
tables['user_event_table'] = user_event_table
tables['company_event_table'] = company_event_table

# write events into bq
def write_rows(table,rows):
    write_table = tables[table]
    write_table.reload()
    write_table.insert_data(rows)

# write events into bq
def add_event(table,row):
    # change to use current partition
    logging.info("user_events${}".format(datetime.now().strftime('%Y%m%d')))
    user_event_table = dataset.table("user_events${}".format(datetime.now().strftime('%Y%m%d')))
    company_event_table = dataset.table("company_events${}".format(datetime.now().strftime('%Y%m%d')))

    if table == "company":
        company_event_table.reload()
        company_event_table.insert_data(row)
    elif table == "user":
        user_event_table.reload()
        user_event_table.insert_data(row)

# wait for async job to complete
def wait_for_job(job):
    while True:
        try:
            job.reload()
            if job.state == 'DONE':
                if job.error_result:
                    raise RuntimeError(job.errors)
                return
        except:
            logging.info("bq error; trying agian")
        time.sleep(1)

def do_query(q_name,col_names,company=''):
    if company == '':
        insert = ''
    else:
        insert = "AND company = '{}'".format(company)

    if q_name == 'pct_provisioned_rolling':
        query = queries.queries[q_name].format(insert,insert)
    else:
        query = queries.queries[q_name].format(insert)
    
    logging.info(query)

    query_job = client.run_async_query(str(uuid.uuid4()), query)
    query_job.use_legacy_sql = False
    query_job.begin()

    wait_for_job(query_job)
    qr = query_job.results()
    page_token = None

    result_rows = []
    while True:
        rows, total_rows, page_token = qr.fetch_data(
            max_results=1000,
            page_token=page_token)

        for row in rows:
            tmp_row = {}
            for col_index in range(0,len(col_names)):
                tmp_row[col_names[col_index]] = row[col_index]
            result_rows.append(tmp_row)

        if not page_token:
            break

    return(result_rows)

def create_table_company_events():
    company_event_table.schema = (
        bigquery.SchemaField('date', 'TIMESTAMP'),
        bigquery.SchemaField('type', 'STRING'),
        bigquery.SchemaField('company', 'STRING'),
        bigquery.SchemaField('purchased', 'INTEGER'),
        bigquery.SchemaField('provisioned', 'INTEGER'),
        bigquery.SchemaField('serial_number', 'STRING'),
        bigquery.SchemaField('box_name', 'STRING')
        )
    # company_event_table.partitioning_type = "DAY"
    company_event_table.create()

def reset_company_events():
    company_event_table.delete()
    create_table_company_events()

def create_table_user_events():
    schema = (
        bigquery.SchemaField('date', 'TIMESTAMP'),
        bigquery.SchemaField('type', 'STRING'),
        bigquery.SchemaField('user', 'STRING'),
        bigquery.SchemaField('company', 'STRING'),
        bigquery.SchemaField('call_duration', 'INTEGER'),
        bigquery.SchemaField('call_type', 'STRING'),
        bigquery.SchemaField('call_num_users', 'INTEGER'),
        bigquery.SchemaField('call_os', 'STRING'),
        bigquery.SchemaField('rating', 'INTEGER'),
        bigquery.SchemaField('comment', 'STRING'),
        bigquery.SchemaField('session_id', 'STRING'),
        bigquery.SchemaField('dialin_duration', 'INTEGER'),
        bigquery.SchemaField('ticket_number', 'STRING'),
        bigquery.SchemaField('ticket_driver', 'STRING')
    )
    user_event_table.schema = schema
    user_event_table.partitioning_type = "DAY"
    user_event_table.create()

    user_event_temp_table.schema = schema
    user_event_temp_table.create()
    
def reset_user_events():
    user_event_table.delete()
    create_table_user_events()

def create_userdata_table():
    userdata_table.schema = (
        bigquery.SchemaField('first_name', 'STRING'),
        bigquery.SchemaField('last_name', 'STRING'),
        bigquery.SchemaField('email', 'STRING'),
        bigquery.SchemaField('company', 'STRING'),
        bigquery.SchemaField('offset', 'INTEGER')
        )
    userdata_table.create()

# delete the events tables
def delete_tables():
    user_event_table.delete()
    company_event_table.delete()

# create the events tables
def create_tables():
    create_table_company_events()
    create_table_user_events()

# create utility table with 2 years worth of days
def create_days_table():
    utils_dataset = client.dataset('utils')
    day_table = utils_dataset.table("days")

    if day_table.exists():
        day_table.delete()
        day_table = utils_dataset.table("days")

    day_table.schema = (
        bigquery.SchemaField('bod', 'TIMESTAMP'),
        bigquery.SchemaField('eod', 'TIMESTAMP'),
        )

    day_table.create()

    rows = []
    for day_shift in range (-365,365):
        day_tmp = datetime.now() - timedelta(days = day_shift)
        bod = datetime(day_tmp.year, day_tmp.month, day_tmp.day,0,0,0,0)
        eod = datetime(day_tmp.year, day_tmp.month, day_tmp.day,23,59,59,999)
        row = (bod,eod)
        rows.append(row)
    day_table.insert_data(rows)

def setup():
    dataset.create()
    create_table_company_events()
    create_table_user_events()
    utils_dataset = client.dataset('utils').create()
    create_days_table()