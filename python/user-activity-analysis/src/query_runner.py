from typing import Any, Dict, Iterator

from sqlalchemy import create_engine, text


def stream_rows(
    user: str, password: str, dsn: str, query: str, study_id: int
) -> Iterator[Dict[str, Any]]:
    engine = create_engine(f"oracle+oracledb://{user}:{password}@{dsn}")
    with engine.connect() as conn:
        result = conn.execution_options(stream_results=True).execute(
            text(query), {"study_id": study_id}
        )
        columns = result.keys()
        for row in result:
            yield dict(zip(columns, row))
