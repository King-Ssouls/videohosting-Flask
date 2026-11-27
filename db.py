import psycopg
from psycopg.row import dict_row
from config import Confing


class Database:
    def get_db(self):
        return psycopg.connect(
            **Confing.DB_PARAMS,
              row_factory=dict_row,
              connect_timeout=5,
        )

    def get_categories(self):
        with get_db(self) as connection:
            categories = connection.execute(
                "SELECT id, name FROM categories ORDER BY id"
            ).fetchall()

        return categories

db = Database(Confing, self)

    # пока заглушка на реализацию проверки работы db.py
if __name__ in "__main__":
        categories = db.get_categories(self)

        print("Бд подлючено")
        print("Найдено категорий: ", len(categories))

        for category in categories:
             print (category["id"], category["name"])