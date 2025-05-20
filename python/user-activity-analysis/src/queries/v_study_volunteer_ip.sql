SELECT
  USER_ID,
  STUDY_ID,
  OFFERS_COMPENSATION,
  SOURCE_ADDRESS,
  LOGIN_DATE,
  SHOWED_INTEREST_DATE,
  SHOWED_INTEREST_AFTER_LOGIN_MINS,  
  RN
FROM (
  SELECT
    v.USER_ID, 
    v.STUDY_ID,
    oc.display_text AS offers_compensation,
    l.SOURCE_ADDRESS AS source_address,
    l.SUCCESSFUL_LOGIN_TIME AS login_date,
    v.SHOWED_INTEREST_DATE,
    ROUND((v.SHOWED_INTEREST_DATE - CAST(l.SUCCESSFUL_LOGIN_TIME AS DATE)) * 24 * 60, 2) AS showed_interest_after_login_mins,    
    ROW_NUMBER() OVER (
      PARTITION BY v.ID
      ORDER BY l.SUCCESSFUL_LOGIN_TIME DESC
    ) AS rn
  FROM (
    SELECT * FROM login_audit
    UNION ALL
    SELECT * FROM {backup_schema}.login_audit
  ) l
  RIGHT JOIN study_volunteer v
    ON l.USER_ID = v.USER_ID
   AND l.SUCCESSFUL_LOGIN_TIME IS NOT NULL
   AND l.SUCCESSFUL_LOGIN_TIME <= v.SHOWED_INTEREST_DATE
   AND l.SUCCESSFUL_LOGIN_TIME >= v.SHOWED_INTEREST_DATE - INTERVAL '3' HOUR
  LEFT JOIN (
    SELECT
      spv.study_id,
      lv.display_text
    FROM entity_property ep
    JOIN study_property_value spv
      ON spv.entity_property_id = ep.id
    JOIN study_prop_val_lookup_val spvlv
      ON spvlv.property_value_id = spv.id
    JOIN lookup_value lv
      ON lv.id = spvlv.lookup_value_id
    WHERE ep.name = 'offersCompensation'
  ) oc
    ON oc.study_id = v.STUDY_ID
)
WHERE rn = 1
  AND SOURCE_ADDRESS IS NOT NULL
ORDER BY showed_interest_date DESC, user_id, study_id