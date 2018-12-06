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

from google.cloud import bigquery
from google.cloud import language

import apache_beam as beam

from datetime import datetime
from datetime import timedelta
from datetime import date

from random import randint, uniform

from oauth2client.client import GoogleCredentials
credentials = GoogleCredentials.get_application_default()

import time
import sys
import os

# grab project ID from env variable
# must set this if running locally; autoset in cloud shell
PROJECT = os.environ['DEVSHELL_PROJECT_ID']

DATASET = 'events'
SOURCE = 'user_events'
TARGET = 'current_sentiment'
BUCKET="{}-df".format(PROJECT)
INTERVAL = -3
LIMIT = ''

# return comments from events_table
query = """
SELECT
  company,
  comment
FROM
  `{}.events.user_events`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(),
    INTERVAL {} day)
  AND CURRENT_TIMESTAMP()
  AND TYPE='comment'
{}
""".format(PROJECT,INTERVAL,LIMIT)

def get_stats(sentiment_tuple):
  company = sentiment_tuple[0]
  scores = sentiment_tuple[1]
  num_scores = len(scores)
  negative = 0
  neutral = 0
  positive = 0
  for index in range(0,num_scores):
    if scores[index] < -0.3:
      negative += 1
    elif scores[index] < 0.3:
      neutral += 1
    else:
      positive += 1
  return {'date': datetime.now().strftime("%Y-%m-%d"),'company': company, 'num_neutral': neutral, 'num_negative': negative, 'num_positive': positive, "num_comments": num_scores}

def get_sentiment(comment_tuple):
  language_client = language.Client()
  comments = comment_tuple[1]
  document = language_client.document_from_text(comments)
  annotations = document.annotate_text(include_syntax=False, include_entities=False, include_sentiment=True)

  s_scores = []
  for s in annotations.sentences:
    s_scores.append(s.sentiment.score)

  return (comment_tuple[0],s_scores)

def make_row(comment_tuple):
  return {'company':comment_dict['company'], 'comment': comment_dict['company']}

# utility for showing contents of pcollections
def output(value):
  print value
  return value

def comment_tuple(comment):
  return (comment['company'],comment['comment'])

def comment_doc(comp_comments):
  company = comp_comments[0]
  comments = comp_comments[1]
  s='\n'
  doc = s.join(comments)
  return (company,doc)

def run():

  client = bigquery.Client(project=PROJECT)
  dataset = client.dataset('sentiment')
  dataset.create()

  argv = [
    '--project={0}'.format(PROJECT),
    '--job_name=shq-sentiment-{}'.format(datetime.now().strftime('%Y%m%d%H%M%S')),
    '--requirements_file=requirements.txt',
    '--save_main_session',
    '--staging_location=gs://{0}/staging/'.format(BUCKET),
    '--temp_location=gs://{0}/staging/'.format(BUCKET),
    '--temp_location=gs://{0}/staging/'.format(BUCKET),
    '--runner=DataflowRunner',
  ]

  # create the pipeline
  p = beam.Pipeline(argv=argv)

  schema = 'date:DATE,company:STRING,num_comments:INTEGER,num_positive:INTEGER,num_neutral:INTEGER,num_negative:INTEGER'

  bq_rows = (p
    | 'read comments from BQ' >> beam.io.Read(beam.io.BigQuerySource(query=query,use_standard_sql=True))
    | 'make comment tuples' >> beam.Map(comment_tuple)
    | 'group comments by company' >> beam.GroupByKey()
    | 'build company comment doc' >> beam.Map(comment_doc)
    | 'get sentiment scores' >> beam.Map(get_sentiment)
    | 'get sentiment stats' >> beam.Map(get_stats)
    | 'write into BQ' >> beam.io.Write(beam.io.BigQuerySink(
      '{}:sentiment.thirty_day_summary'.format(PROJECT),
      project = PROJECT,
      schema = schema,
      write_disposition = beam.io.BigQueryDisposition.WRITE_APPEND,
      create_disposition = beam.io.BigQueryDisposition.CREATE_IF_NEEDED)))

  # run the pipeline
  p.run()

if __name__ == '__main__':
   run()
