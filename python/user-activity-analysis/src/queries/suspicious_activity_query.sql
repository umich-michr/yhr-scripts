signup_suspicious AS (
  SELECT 
    source_address,
    COUNT(DISTINCT user_id) AS suspicious_signup_count,
    ROUND((CAST(MAX(created_date) AS DATE) - CAST(MIN(created_date) AS DATE)) * 24 * 60, 2) AS creation_period_mins,
    ROUND((CAST(MAX(user_activation_time) AS DATE) - CAST(MIN(user_activation_time) AS DATE)) * 24 * 60, 2) AS activation_period_mins,
    ROUND(AVG(time_to_activate_mins), 2) AS avg_time_to_activate_mins
  FROM v_user_activation_time
  GROUP BY source_address
  HAVING COUNT(DISTINCT user_id) > 1
),
-- Aggregate suspicious interest by study/IP
interested_suspicious AS (
  SELECT 
    study_id,
    offers_compensation,
    source_address,
    COUNT(DISTINCT user_id) AS suspicious_interested_count,
    ROUND((MAX(showed_interest_date) - MIN(showed_interest_date)) * 24 * 60, 2) AS interest_period_mins,
    ROUND(AVG(showed_interest_after_login_mins), 2) AS avg_time_to_show_interest_mins
  FROM v_study_volunteer_ip
  GROUP BY study_id, source_address, offers_compensation
  HAVING COUNT(DISTINCT user_id) > 1
)
SELECT
  v.USER_ID,
  CASE
    WHEN REGEXP_LIKE(
      au.user_name,
      '^' ||
      REGEXP_REPLACE(au.first_name, '([.\^\$\*\+\?\(\)\|\{\}\[\]\\\\])', '\\\1') ||
      '(?:\\.|_|\+|\\-)?' ||
      REGEXP_REPLACE(au.last_name, '([.\^\$\*\+\?\(\)\|\{\}\[\]\\\\])', '\\\1') ||
      '(?:\\.|_|\+|\\-)?' ||
      '[0-9]*@.+$',
      'i'
    )
    OR REGEXP_LIKE(
      au.user_name,
      '^' ||
      REGEXP_REPLACE(au.last_name, '([.\^\$\*\+\?\(\)\|\{\}\[\]\\\\])', '\\\1') ||
      '(?:\\.|_|\+|\\-)?' ||
      REGEXP_REPLACE(au.first_name, '([.\^\$\*\+\?\(\)\|\{\}\[\]\\\\])', '\\\1') ||
      '(?:\\.|_|\+|\\-)?' ||
      '[0-9]*@.+$',
      'i'
    )
    THEN 'True'
    ELSE 'False'
  END AS matches_name_pattern,
  v.STUDY_ID,
  v.offers_compensation,
  v.SOURCE_ADDRESS AS INTEREST_SOURCE_ADDRESS,
  i.suspicious_interested_count,
  i.interest_period_mins,
  i.avg_time_to_show_interest_mins,
  u.SOURCE_ADDRESS AS ACTIVATION_SOURCE_ADDRESS,
  NVL(s.suspicious_signup_count, 0) AS suspicious_signup_count,
  NVL(s.creation_period_mins, 0) AS creation_period_mins,
  NVL(s.activation_period_mins, 0) AS activation_period_mins,
  NVL(s.avg_time_to_activate_mins, 0) AS avg_time_to_activate_mins
FROM v_study_volunteer_ip v
LEFT JOIN v_user_activation_time u
  ON v.user_id = u.user_id
JOIN app_user au
  ON au.id=v.user_id
JOIN interested_suspicious i
  ON v.study_id = i.study_id
 AND v.source_address = i.source_address
LEFT JOIN signup_suspicious s
  ON u.source_address = s.source_address
WHERE 1=1
-- APPEND STUDY_ID_FILTER_HERE
ORDER BY
  i.suspicious_interested_count DESC,
  v.user_id,
  v.study_id,
  v.source_address