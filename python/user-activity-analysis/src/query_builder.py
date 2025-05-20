import os


def _load_query(filename: str, backup_schema: str) -> str:
    with open(filename, "r") as f:
        sql = f.read()
    return sql.replace("{backup_schema}", backup_schema)


def _build_suspicious_activity_query(
    v_study_volunteer_ip: str,
    v_user_activation_time: str,
    suspicious_activity_query: str,
) -> str:
    combined_sql = f"""
    WITH
    v_study_volunteer_ip AS (
        {v_study_volunteer_ip}
    ),
    v_user_activation_time AS (
        {v_user_activation_time}
    )
    {suspicious_activity_query}
    """
    return combined_sql


def _add_study_id_filter(query: str) -> str:
    if "-- APPEND STUDY_ID_FILTER_HERE" in query:
        return query.replace(
            "-- APPEND STUDY_ID_FILTER_HERE", "AND v.study_id = :study_id"
        )
    else:
        order_by_idx = query.lower().rfind("order by")
        if order_by_idx != -1:
            return (
                query[:order_by_idx]
                + "AND v.study_id = :study_id\n"
                + query[order_by_idx:]
            )
        return query + "\nAND v.study_id = :study_id\n"


def build_database_query(backup_schema: str, queries_dir: str) -> str:
    v_study_volunteer_ip = _load_query(
        os.path.join(queries_dir, "v_study_volunteer_ip.sql"), backup_schema
    )
    v_user_activation_time = _load_query(
        os.path.join(queries_dir, "v_user_activation_time.sql"), backup_schema
    )
    suspicious_activity_ctes_and_select = _load_query(
        os.path.join(queries_dir, "suspicious_activity_query.sql"), backup_schema
    )

    # Ensure the suspicious_activity_query.sql does not start with a comma or whitespace
    suspicious_activity_ctes_and_select = suspicious_activity_ctes_and_select.lstrip()
    # Add a comma before the suspicious_activity_query.sql content if not already present
    if not suspicious_activity_ctes_and_select.startswith(","):
        suspicious_activity_ctes_and_select = "," + suspicious_activity_ctes_and_select

    query = f"""
    WITH
    v_study_volunteer_ip AS (
        {v_study_volunteer_ip}
    ),
    v_user_activation_time AS (
        {v_user_activation_time}
    )
    {suspicious_activity_ctes_and_select}
    """
    return _add_study_id_filter(query)
