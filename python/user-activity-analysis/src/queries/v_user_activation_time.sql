SELECT
  d.USER_ID,
  la.source_address,
  round((cast(la.user_activation_time as date)-cast(d.CREATED_DATE as date))*24*60,2) time_to_activate_mins,
  d.CREATED_DATE,
  la.user_activation_time
FROM
  db_user_auth_detail d
LEFT JOIN (
  SELECT
    l.USER_ID,
    MIN(l.SUCCESSFUL_LOGIN_TIME) AS user_activation_time,
    MIN(l.source_address) KEEP (DENSE_RANK FIRST ORDER BY l.SUCCESSFUL_LOGIN_TIME) AS source_address
  FROM (
    SELECT * FROM login_audit
    UNION ALL
    SELECT * FROM {backup_schema}.login_audit
  ) l
  JOIN db_user_auth_detail d2 ON l.USER_ID = d2.USER_ID
  WHERE
    l.SUCCESSFUL_LOGIN_TIME IS NOT NULL
    AND l.SUCCESSFUL_LOGIN_TIME >= d2.CREATED_DATE
    AND l.SUCCESSFUL_LOGIN_TIME < d2.CREATED_DATE + INTERVAL '7' DAY
  GROUP BY
    l.USER_ID
) la ON d.USER_ID = la.USER_ID
WHERE la.user_activation_time IS NOT NULL
ORDER BY la.user_activation_time DESC