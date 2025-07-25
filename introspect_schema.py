"""
introspect_schema.py

Utility script to inspect and print all tables and their columns
from the IQ database, using SQLAlchemy reflection.
"""

import os
from sqlalchemy import create_engine, MetaData
from dotenv import load_dotenv


def main():
    # Load DB connection URL from .env
    load_dotenv()
    db_url = os.getenv("IQ_DB_AUTH")
    if not db_url:
        raise RuntimeError("IQ_DB_AUTH is not set in the environment")

    # Reflect metadata from the database
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Print schema: tables and their columns
    for table_name, table in metadata.tables.items():
        print(f"Table: {table_name}")
        for col in table.columns:
            print(f"  - {col.name:<20} {col.type!s:<15} nullable={col.nullable}")
        print()


if __name__ == "__main__":
    main()
