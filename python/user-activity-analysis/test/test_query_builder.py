import pytest

from src.query_builder import (_add_study_id_filter,
                               _build_suspicious_activity_query, _load_query,
                               build_database_query)


@pytest.fixture
def sql_file(tmp_path):
    """Helper to create a temp sql file with given content and return its path."""

    def _create(filename, content):
        file_path = tmp_path / filename
        file_path.write_text(content)
        return str(file_path)

    return _create


def test_load_query_replaces_backup_schema(sql_file):
    file_path = sql_file(
        "v_study_volunteer_ip.sql",
        "SELECT * FROM table WHERE schema = '{backup_schema}';",
    )

    result = _load_query(file_path, "my_backup")

    assert "{backup_schema}" not in result
    assert "my_backup" in result


def test_get_final_query_combines_sql(sql_file):
    view1 = _load_query(
        sql_file("v_study_volunteer_ip.sql", "SELECT 1 AS a"), "backup1"
    )
    view2 = _load_query(
        sql_file("v_user_activation_time.sql", "SELECT 2 AS b"), "backup2"
    )
    final = _load_query(
        sql_file(
            "final_suspicious_activity_query.sql",
            "SELECT * FROM v_study_volunteer_ip JOIN v_user_activation_time",
        ),
        "backup3",
    )

    result = _build_suspicious_activity_query(view1, view2, final)

    assert "v_study_volunteer_ip AS" in result
    assert view1 in result
    assert "v_user_activation_time AS" in result
    assert view2 in result
    assert final in result


def test_add_study_id_filter_with_marker(sql_file):
    file_path = sql_file(
        "final_query.sql",
        "SELECT * FROM table\n-- APPEND STUDY_ID_FILTER_HERE\nORDER BY id",
    )
    query = _load_query(file_path, "backup_schema")

    result = _add_study_id_filter(query)

    assert "-- APPEND STUDY_ID_FILTER_HERE" not in result
    assert "AND v.study_id = :study_id" in result
    assert result.index("AND v.study_id = :study_id") < result.lower().index("order by")


def test_add_study_id_filter_with_order_by(sql_file):
    file_path = sql_file("order_by_query.sql", "SELECT * FROM table\nORDER BY id")
    query = _load_query(file_path, "backup_schema")

    result = _add_study_id_filter(query)

    assert "AND v.study_id = :study_id" in result
    assert result.index("AND v.study_id = :study_id") < result.lower().index("order by")


def test_add_study_id_filter_no_marker_no_order_by(sql_file):
    file_path = sql_file("plain_query.sql", "SELECT * FROM table")
    query = _load_query(file_path, "backup_schema")

    result = _add_study_id_filter(query)

    assert result.strip().endswith("AND v.study_id = :study_id")


def test_build_database_query(tmp_path):
    # Create dummy SQL files in the temp directory
    (tmp_path / "v_study_volunteer_ip.sql").write_text(
        "SELECT * FROM volunteer WHERE schema = '{backup_schema}'"
    )
    (tmp_path / "v_user_activation_time.sql").write_text(
        "SELECT * FROM activation WHERE schema = '{backup_schema}'"
    )
    (tmp_path / "suspicious_activity_query.sql").write_text(
        "SELECT * FROM v_study_volunteer_ip JOIN v_user_activation_time -- APPEND STUDY_ID_FILTER_HERE ORDER BY id"
    )

    backup_schema = "test_schema"
    queries_dir = str(tmp_path)
    query = build_database_query(backup_schema, queries_dir)

    assert "test_schema" in query
    assert "AND v.study_id = :study_id" in query
    assert "WITH" in query
    assert "v_study_volunteer_ip AS" in query
    assert "v_user_activation_time AS" in query
    assert "JOIN v_user_activation_time" in query
