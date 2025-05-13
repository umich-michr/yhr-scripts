STUDY_INTEREST_QUERY = """
WITH ranked_logins AS (
    SELECT 
        la.USER_ID,
        la.SOURCE_ADDRESS,
        sv.STUDY_ID,
        ROW_NUMBER() OVER (
            PARTITION BY la.USER_ID, sv.SHOWED_INTEREST_DATE 
            ORDER BY ABS(cast(SHOWED_INTEREST_DATE as date) - cast(SUCCESSFUL_LOGIN_TIME as date)) 
        ) AS login_rank
    FROM 
        login_audit la
    JOIN 
        study_volunteer sv ON la.USER_ID = sv.USER_ID
    WHERE 
        sv.SHOWED_INTEREST_DATE IS NOT NULL
        AND la.SUCCESSFUL_LOGIN_TIME <= sv.SHOWED_INTEREST_DATE
),
study_interest AS (
    SELECT 
        USER_ID,
        SOURCE_ADDRESS,
        STUDY_ID
    FROM 
        ranked_logins
    WHERE 
        login_rank = 1
),
compensation_studies AS (
    SELECT 
        spv.study_id AS study_id,
        lv.name AS offers_compensation
    FROM 
        entity_property ep,
        study_property_value spv,
        STUDY_PROP_VAL_LOOKUP_VAL spvlv,
        lookup_value lv
    WHERE 
        ep.name = 'offersCompensation'
        AND spv.entity_property_id = ep.id
        AND spvlv.PROPERTY_VALUE_ID = spv.id
        AND spvlv.LOOKUP_VALUE_ID = lv.id
)
SELECT 
    si.STUDY_ID,
    COALESCE(cs.offers_compensation, 'No') AS offers_compensation,
    si.SOURCE_ADDRESS,
    COUNT(si.USER_ID) AS user_count,
    LISTAGG(si.USER_ID, ', ') WITHIN GROUP (ORDER BY si.USER_ID) AS user_ids
FROM 
    study_interest si
LEFT JOIN 
    compensation_studies cs ON si.STUDY_ID = cs.study_id
GROUP BY 
    si.STUDY_ID,
    si.SOURCE_ADDRESS,
    cs.offers_compensation
ORDER BY 
    user_count DESC, study_id
"""
