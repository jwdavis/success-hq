#!/bin/bash

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

# enable apis
gcloud services enable translate.googleapis.com
gcloud services enable language.googleapis.com
gcloud services enable dataflow.googleapis.com
gcloud services enable bigquery-json.googleapis.com

# create dataflow bucket
gsutil mb gs://$DEVSHELL_PROJECT_ID-df

# create virtual environment
virtualenv  --python=/usr/bin/python ~/success-hq/shq
source ~/success-hq/shq/bin/activate

# install python stuff
pip install --upgrade pip==9.0.1
pip install --upgrade -r req-1.txt
pip install --upgrade -r req-2.txt -t lib

# create app engine app
gcloud app create --region=us-central --quiet
gcloud app deploy app_web/app.yaml api_events/app.yaml queue.yaml index.yaml --quiet

# run dataflow jobs
cd demo_data
curl https://$DEVSHELL_PROJECT_ID.appspot.com/setup?what=setup_bq
python datastore_pipeline.py
python sentiment.py

# remove unneeded bq table
bq rm -f -t events.user_events_load
