import zipfile

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base


@pytest.fixture
def db():
    # Fast isolated unit tests. Actual PostgreSQL startup/migrations are checked separately.
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def archive(tmp_path):
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w") as output:
        output.writestr(
            "ml-latest-small/movies.csv",
            'movieId,title,genres\n1,"Example, The (2000)",Drama|Comedy\n'
            "2,Another (2001),(no genres listed)\n",
        )
        output.writestr(
            "ml-latest-small/ratings.csv",
            "userId,movieId,rating,timestamp\n1,1,4.5,1000\n2,2,3.0,1001\n",
        )
    return path
