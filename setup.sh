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
echo "Enabling necessary services..."
gcloud services enable translate.googleapis.com
gcloud services enable language.googleapis.com
gcloud services enable dataflow.googleapis.com
gcloud services enable bigquery-json.googleapis.com

# create dataflow bucket
echo "Creating GCS bucket..."
gsutil mb gs://$DEVSHELL_PROJECT_ID-df

# create virtual environment
echo "Creating Virtual Environment..."
virtualenv  --python=/usr/bin/python ~/success-hq/shq
source ~/success-hq/shq/bin/activate

# install python stuff
echo "Updating pip..."
pip install --upgrade pip==9.0.1

echo "Installing packages in Cloud Shell"
pip install --upgrade -r req-1.txt

echo "Installing packages into lib (to be vendored into GAE)"
pip install --upgrade -r req-2.txt -t lib

# fix protobuf problem in cloud shell
echo "Uninstalling protobuf in Cloud Shell"
pip uninstall protobuf -y

echo "Reinstalling protobuf in Cloud Shell"
pip install protobuf -q

# create app engine app
echo "Creating GAE app..."
gcloud app create --region=us-central --quiet

echo "Deploying to GAE..."
gcloud app deploy app_web/app.yaml api_events/app.yaml queue.yaml index.yaml --quiet

# run dataflow jobs
cd demo_data

echo "Calling setup URL to create datasets and tables..."
curl https://$DEVSHELL_PROJECT_ID.appspot.com/setup?what=setup_bq

echo "Running Dataflow pipeline to generate sample data..."
python datastore_pipeline.py

echo "Running Dataflow pipeline to do sentiment analysis"
python sentiment.py

# remove unneeded bq table

echo "Removing unneeded BQ table"
bq rm -f -t events.user_events_load
