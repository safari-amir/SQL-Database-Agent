from sqlalchemy import inspect

def get_database_schema(engine):
    inspector = inspect(engine)
    schema = ""
    for table_name in inspector.get_table_names():
        schema += f"Table: {table_name}\n"
        for column in inspector.get_columns(table_name):
            col = f"- {column['name']}: {str(column['type'])}"
            if column.get("primary_key"):
                col += ", Primary Key"
            if column.get("foreign_keys"):
                fk = list(column["foreign_keys"])[0]
                col += f", Foreign Key to {fk.column.table.name}.{fk.column.name}"
            schema += col + "\n"
        schema += "\n"
    return schema

