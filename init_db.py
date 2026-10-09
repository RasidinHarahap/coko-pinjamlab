from pathlib import Path
from database import connect, database_path


def initialize():
    with connect() as conn:
        conn.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
    print(f'Database SQLite siap: {database_path().name}')


if __name__ == '__main__':
    initialize()
