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

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache

import jinja2

class BaseHandler(webapp.RequestHandler):
    context = {}
    def initialize(self, request, response):
        self.populateContext()
        super(BaseHandler, self).initialize(request, response)

    def populateContext(self):
        user = users.get_current_user()

        if user:
            self.context['logged_in'] = True
            self.context['is_admin'] = users.is_current_user_admin()

    def render(self, template_name):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('views'))
        template = env.get_template(template_name)
        self.response.out.write(template.render(self.context))

def UpdateMemcache(key,value_to_encode):
    data = memcache.get(key)
    if data is not None:
        memcache.replace(key,json.dumps(value_to_encode))
    else:
        memcache.add(key,json.dumps(value_to_encode))
