 #!/bin/bash

# remove from app_web
rm app_web/bq
rm app_web/datastore
rm app_web/utils.py
rm app_web/lib

# # add to app_web
cd app_web
ln -s ../lib lib
ln -s ../bq bq
ln -s ../datastore datastore
ln -s ../utils.py utils.py

# # remove from api_events
rm api_events/bq
rm api_events/datastore
rm api_events/utils.py
rm api_events/lib

# # add to api_events
cd ../api_events
ln -s ../lib lib
ln -s ../bq bq
ln -s ../datastore datastore
ln -s ../utils.py utils.py

# # remove from api_reports
rm api_reports/bq
rm api_reports/datastore
rm api_reports/utils.py
rm api_reports/lib

# # add to api_reports
cd ../api_reports
ln -s ../lib lib
ln -s ../bq bq
ln -s ../datastore datastore
ln -s ../utils.py utils.py
