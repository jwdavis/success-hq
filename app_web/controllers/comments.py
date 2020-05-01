# -*- coding: utf-8 -*-
from __future__ import division

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


import utils
import logging
import json

from google.appengine.ext import ndb
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

from google.cloud import translate
from google.cloud import language

from bq import bq

sample_comments = [
    u"This was terrific. I hated it.",
    u"C'était bien. L'audio était un peu grinçant.",
    u"Me decepcionó que no hay soporte para Linux.",
    u"超棒",
    u"Jambo hili ni jambo la kushangaza! Ilikuwa ni kama mimi nilikuwa huko."
]

translate_client = translate.Client()
language_client = language.Client()

# results = bq.do_query('comments_last_month',['comment'],'successops.com')

class show(utils.BaseHandler):
    def get(self):
        output = []
        for comment in sample_comments:

            # determine language and translate
            translate_client = translate.Client()
            tranlastion_result = translate_client.translate(comment,target_language='en')
            translated_comment = tranlastion_result['translatedText']

            # do sentiment analysis ine english
            document = language_client.document_from_text(translated_comment)
            sentiment = document.analyze_sentiment().sentiment
            score = sentiment.score
            magnitude = sentiment.magnitude

            # pick color coding for sentiment
            if score > .5 and magnitude > .5:
                alert_class = "alert-success"
            elif score < -.5 and magnitude > .5:
                alert_class = "alert-danger"
            elif score < 0:
                alert_class = "alert-warning"
            else:
                alert_class = "alert-info"

            # construct output data
            output.append({
                "original": comment.encode('ascii','xmlcharrefreplace'),
                "translated": translated_comment.encode('ascii','xmlcharrefreplace'),
                "score": score,
                "magnitude": magnitude,
                "alert_class": alert_class
                })

        # render page
        self.context['comments'] = output
        self.render('comments.html')



