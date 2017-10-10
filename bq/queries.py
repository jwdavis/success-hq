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


queries = {}

queries['comments_last_month'] = """
SELECT
  comment
FROM
  events.user_events
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(),
    INTERVAL -30 day)
  AND CURRENT_TIMESTAMP()
  AND TYPE='comment'
  {}
"""

queries['active_users_sliding_7']="""
WITH
  sdau_raw AS (
  SELECT
    day,
    COUNT(DISTINCT(user)) seven_day_active_users
  FROM (
    SELECT
      DATE(days.bod) day,
      calls.user user,
      COUNT(calls.date) calls
    FROM (
      SELECT
        *
      FROM
        `utils.days`
      WHERE
        eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -29 DAY)
        AND bod < CURRENT_TIMESTAMP()) days
    CROSS JOIN (
      SELECT
        *
      FROM
        `events.user_events`
      WHERE
        _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day) AND CURRENT_TIMESTAMP()
        AND type="call"
        {}) calls
    WHERE
      calls.date >= TIMESTAMP_ADD(days.bod, INTERVAL -7 DAY)
      AND calls.date < days.eod
    GROUP BY
      day,
      user)
  GROUP BY
    day)
SELECT
  days.day as day,
  ifnull(sdau_raw.seven_day_active_users,0) as users
FROM (
  SELECT
    DATE(bod) AS day
  FROM
    `utils.days`
  WHERE
    eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -29 DAY)
    AND bod < CURRENT_TIMESTAMP()) days
LEFT JOIN
  sdau_raw
ON
  sdau_raw.day = days.day
ORDER BY
  day

"""

queries['ratings_sliding_7']="""
SELECT
  *
FROM (
  SELECT
    day,
    round(AVG(avg_rating) OVER (ORDER BY day ROWS BETWEEN 7 PRECEDING AND CURRENT row),1) AS avg_rating,
    SUM(num_ratings) OVER (ORDER BY day ROWS BETWEEN 7 PRECEDING AND CURRENT row) AS num_ratings
  FROM (
    SELECT
      p37.day day,
      ifnull(rlw.avg_rating,
        0) AS avg_rating,
      ifnull(rlw.num_ratings,
        0) AS num_ratings
    FROM (
      SELECT
        DATE(eod) AS day
      FROM
        `utils.days`
      WHERE
        bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day)
        AND bod <= CURRENT_TIMESTAMP()) p37
    LEFT JOIN (
      SELECT
        DATE(date) AS day,
        AVG(rating) AS avg_rating,
        COUNT(rating) AS num_ratings
      FROM
        `events.user_events`
      WHERE
        _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day) AND CURRENT_TIMESTAMP()
        AND type='rating'
        {}
      GROUP BY
        day) rlw
    ON
      rlw.day = p37.day))
WHERE
  day > DATE_ADD(CURRENT_DATE(), INTERVAL -30 day)
ORDER BY
  day
"""

queries['pct_provisioned_rolling']="""
SELECT
  prov.day AS day,
  round(prov.provisioned/purch.purchased*100,1) as pct_provisioned
from
  (SELECT
    days.bod day,
    SUM(b.provisioned) provisioned
  FROM (
    SELECT
      *
    FROM
      `utils.days`
    WHERE
      eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 DAY)
      AND bod < CURRENT_TIMESTAMP()) days
  CROSS JOIN (
    SELECT
      *
    FROM
      `events.company_events`
    WHERE
      type="provisioned"
      {}) b
  WHERE
    b.date < days.eod
  GROUP BY
    day,
    company) AS prov
LEFT JOIN (
  SELECT
    days.bod day,
    SUM(b.purchased) purchased
  FROM (
    SELECT
      *
    FROM
      `utils.days`
    WHERE
      eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 DAY)
      AND bod < CURRENT_TIMESTAMP()) days
  CROSS JOIN (
    SELECT
      *
    FROM
      `events.company_events`
    WHERE
      type="purchased"
      {}) b
  WHERE
    b.date < days.eod
  GROUP BY
    day) AS purch
ON
  purch.day = prov.day
ORDER BY
  day
"""

queries['provisioned_boxes_rolling']="""
SELECT
  days.bod day,
  SUM(b.provisioned) provisioned
FROM (
  SELECT
    *
  FROM
    `utils.days`
  WHERE
    eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 DAY)
    AND bod < CURRENT_TIMESTAMP()) days
CROSS JOIN (
  SELECT
    *
  FROM
    `events.company_events`
  WHERE
    type="provisioned"
    {}) b
WHERE
  b.date < days.eod
GROUP BY
  day,
  company
ORDER BY
  day,
  company
"""

queries['purchased_boxes_rolling']="""
SELECT
  days.bod day,
  SUM(b.purchased) purchased
FROM (
  SELECT
    *
  FROM
    `utils.days`
  WHERE
    eod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 DAY)
    AND bod < CURRENT_TIMESTAMP()) days
CROSS JOIN (
  SELECT
    *
  FROM
    `events.company_events`
  WHERE
    type="purchased"
    {}) b
WHERE
  b.date < days.eod
GROUP BY
  day,
  company
ORDER BY
  day,
  company
"""

queries['reg_users_rolling'] = """
WITH
  reg AS (
  SELECT
    ifnull(ru.day,
      days.day) AS day,
    ifnull(ru.users,
      0) AS users
  FROM (
    SELECT
      DATE(eod) AS day
    FROM
      `utils.days`
    WHERE
      bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 day)
      AND bod <= CURRENT_TIMESTAMP()) days
  FULL JOIN (
    SELECT
      day,
      COUNT(day) AS users
    FROM (
      SELECT
        DATE(date) AS day
      FROM
        `events.user_events`
      WHERE
        type='register'
        {})
    GROUP BY
      day) ru
  ON
    days.day = ru.day),
  total_reg AS (
  SELECT
    day,
    SUM(users) OVER (ORDER BY day) AS users
  FROM
    reg ),
  days AS (
  SELECT
    DATE(eod) AS day
  FROM
    `utils.days`
  WHERE
    bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -30 day)
    AND bod <= CURRENT_TIMESTAMP())
SELECT
  days.day AS day,
  total_reg.users AS reg_users
FROM
  days
LEFT JOIN
  total_reg
ON
  days.day = total_reg.day
ORDER BY
  day
"""

queries['calls_sliding_7'] = """
SELECT
  * from(
  SELECT
    day,
    SUM(calls) OVER (ORDER BY day ROWS BETWEEN 7 PRECEDING AND CURRENT row) as calls
  FROM (
    SELECT
      p37.day day,
      ifnull(clw.calls,
        0) AS calls
    FROM (
      SELECT
        DATE(eod) AS day
      FROM
        `utils.days`
      WHERE
        bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day)
        AND bod <= CURRENT_TIMESTAMP()) p37
    LEFT JOIN (
      SELECT
        day,
        COUNT(day) AS calls
      FROM (
        SELECT
          DATE(date) AS day
        FROM
          `events.user_events`
        WHERE
          ((_PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day) AND CURRENT_TIMESTAMP()) OR _PARTITIONTIME IS NULL)
          AND type='call'
          {})
      GROUP BY
        day) clw
    ON
      clw.day = p37.day))
WHERE
  day > DATE_ADD(CURRENT_DATE(), INTERVAL -30 day)
ORDER BY
  day"""

queries['dialin_sliding_7'] = """
SELECT
  * from(
  SELECT
    day,
    SUM(dialins) OVER (ORDER BY day ROWS BETWEEN 7 PRECEDING AND CURRENT row) as dialins
  FROM (
    SELECT
      p37.day day,
      ifnull(dlw.dialins,
        0) AS dialins
    FROM (
      SELECT
        DATE(eod) AS day
      FROM
        `utils.days`
      WHERE
        bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day)
        AND bod <= CURRENT_TIMESTAMP()) p37
    LEFT JOIN (
      SELECT
        day,
        COUNT(day) AS dialins
      FROM (
        SELECT
          DATE(date) AS day
        FROM
          `events.user_events`
        WHERE
          _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day) AND CURRENT_TIMESTAMP()
          AND type='dialin'
          {})
      GROUP BY
        day) dlw
    ON
      dlw.day = p37.day))
WHERE
  day > DATE_ADD(CURRENT_DATE(), INTERVAL -30 day)
ORDER BY
  day"""

queries['support_sliding_7'] = """
SELECT
  * from(
  SELECT
    day,
    SUM(support_tickets) OVER (ORDER BY day ROWS BETWEEN 7 PRECEDING AND CURRENT row) as support_tickets
  FROM (
    SELECT
      p37.day day,
      ifnull(slw.support_tickets,
        0) AS support_tickets
    FROM (
      SELECT
        DATE(eod) AS day
      FROM
        `utils.days`
      WHERE
        bod > TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day)
        AND bod <= CURRENT_TIMESTAMP()) p37
    LEFT JOIN (
      SELECT
        day,
        COUNT(day) AS support_tickets
      FROM (
        SELECT
          DATE(date) AS day
        FROM
          `events.user_events`
          WHERE
          _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -37 day) AND CURRENT_TIMESTAMP()
          AND type='support_ticket'
          {})
      GROUP BY
        day) slw
    ON
      slw.day = p37.day))
WHERE
  day > DATE_ADD(CURRENT_DATE(), INTERVAL -30 day)
ORDER BY
  day"""

queries['comments_last_week'] = """
SELECT
  comment,
  user,
  date
FROM
  `events.user_events`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -7 day) AND CURRENT_TIMESTAMP()
  AND type='comment'
  {}
ORDER BY 
  date DESC
LIMIT
  8
"""

queries['purchased'] = """
SELECT
  sum(purchased) as purchased
FROM
  `events.company_events`
WHERE
  type = 'purchased'
  {}
"""

queries["calls_by_type_last_week"]="""
SELECT
  call_type, 
  COUNT(call_type) as calls
FROM
  `events.user_events`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -7 day) AND CURRENT_TIMESTAMP()
  AND type="call"
  {}
GROUP BY 
  call_type
"""

queries["calls_by_size_last_week"]="""
SELECT
  call_num_users, 
  COUNT(call_num_users) as calls
FROM
  `events.user_events`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -7 day) AND CURRENT_TIMESTAMP()
  AND type="call"
  {}
GROUP BY 
  call_num_users
"""

queries["calls_by_os_last_week"]="""
SELECT
  call_os, 
  COUNT(call_os) as calls
FROM
  `events.user_events`
WHERE
  _PARTITIONTIME BETWEEN TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -7 day) AND CURRENT_TIMESTAMP()
  AND type="call"
  {}
GROUP BY 
  call_os
"""