# Setup

* Create a project to contain resources used in this demo
* Open GCP Cloud Shell pointed at demo project
* Clone repo to cloud shell
```
git clone https://github.com/jwdavis/success-hq
```
* Run the setup script.
```
cd ~/success-hq
. ./setup.sh
```

# Demo

## Overview

* Describe purpose of app
* Show home page
* Show customer dashboard
	* Note that in real world, cards would be cached
* Explain 30 day trends and sliding windows
* Show BQ behind the scenes
* Show Datastore behind the scenes
* Show App Engine details
	* Multiple services
	* Multiple versions
	* Delete front-end instances to show scale to zero
	* Reload home page and show instance now running

## Scaling

* Show default service scaling
	* In Console, show **default** service instances; kill any instances that are running
	* Using something like Apache Bench, generate a load of the front-end. e.g. `ab -n 10000 -c 50 https://<project-id>.appspot.com/`
	* Refresh instances page several times to show new instances and the requests they are handling

* Show api-events service sclaing
	* In Console, show **api_events** service instances
	* Visit `http://<project-id>.appspot.com/get_busy`
	* Click on **Start 1000**
	* Click **Refresh** button on the instances page a few times to show new requests, but no scaling
	* In app, click on **Start 1000000**
	* In Console, show requests ramping up and instances scaling
	* While load generator is running (60 seconds) go back to a customer dashboard and refresh 1-2 times; **calls/week** should increase showing live data

## App admin
* Show versions and traffic splitting
	* Change contents of home page or make another interesting change
	* Redeploy app
	* Show new feature by visting home page
	* Roll back to previous version and show no new feature
	* Split traffic and discuss A/B testing
