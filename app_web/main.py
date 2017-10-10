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

import webapp2
import utils
import logging
import loadgen
import setup
from controllers import home, customer, oops, get_busy, comments

app = webapp2.WSGIApplication([
    ('/setup',setup.setup_factory),
    ('/comments',comments.show),
    ('/load_gen',loadgen.go),
    ('/go_long',loadgen.go_long),
    ('/get_busy',get_busy.show),
    (r'/customer/(.*)',customer.show),
    ('/',home.show),
    (r'.*', oops.show)],
    debug=True)