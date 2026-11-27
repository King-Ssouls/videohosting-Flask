import psycopg
from psycopg.row import dict_row
from config import Confing


class Database:
    #РЕАЛИЗОВАТЬ ОБЩЙИ ЗАПРОС НА ВИДЕО. ОТДЕЛЬНО СЧИТАТЬ КОМЕНТЫ И РЕАЦИИИ
    VIDEO_SELECT =  """
        SELECT v.* 

    """

    def __init__(self, db_params=None):
        if db_params is None:
            db_params = Confing.DB_PAREMS

        self.db_params = dict(db_params)


    def get_db(self):
        return psycopg.connect(
            **self.db_params,
            row_factory=dict_row,
            connect_timeout=5
        )

    # служебные методы для сокращения кода
    def _fetch_one(self, query, params=()):
        with self.get_db() as connection:
            return connection.execute(query, params).fetchone()

    def _fetch_all(self, query, params=()):
        with self.get_db() as connection:
            return connection.execute(query, params).fetchall()

    def _execute(self, query, params=()):
        with self.get_db() as connection:
            return connection.execute(query, params).rowcount

    def _insert_user(self, nickname, email, password_hash, role):
        return self._fetch_one(
            """
                INSERT INTO users (nickname, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
            (nickname.strip(), email.strip().lower, password_hash, role)
        )
    
        return user["id"]


    # методы для юзера
    def get_user_id(self, user_id):
        return self._fetch_one(
            """
                SELECT id, nickname, email, role, created_at
                FROM users
                WHERE id = %s
            """,
            (user_id,),
        )

    def get_user_nickname(self, nickname):
        return self._fetch_one(
            """
                SELECT id, nickname, email, role, created_at
                FROM users
                WHERE nickname = %s
            """,
            (nickname.strip(),),
        )

    def get_user_email(self, email):
        return self._fetch_one(
            """
                SELECT id, nickname, email, role, created_at
                FROM users
                WHERE LOWER(email) = %s
            """,
            (email.strip().lower(),),
        )

    def create_user(self, nickname, email, password_hash):
        return self._insert_user(nickname, email, password_hash, "user")

    def create_admin(self, nickname, email, password_hash):
        return self._insert_user(nickname, email, password_hash, "admin")

    # функции под категории

    def get_categories(self):
        return self._fetch_all(
            "SELECT id, name FROM categories ORDER BY id"
        )

    def get_categories_id(self, categories_id):
        return self._fetch_one(
            "SELECT id, name FROM category WHERE id = %s"
        )


    #функции для видеороликов

    def create_video(self, user_id, category_id, title, file_name, description=""):
        video = self._fetch_one(
            """
                INSERT INTO videos (
                user_id, category-id, title, file_name, description
                )
                VALUES (%s, %s, %s, %s, %s, )
                RETURNING id
            """, 
            (user_id, category_id, title, file_name, description)
        )
        return video["id"]

    def get_latest_videos(self):
        return self._fetch_all(
            self.VIDIO_SELECT + 
            """
                WHERE v.restriction = 'none'
                ORDER BY v.created_at DESC, v.id DESC
                LIMIT 10
            """
        )

    def get_user_video(self, user_id):
        return self._fetch_all(
            self.VIDEO_SELECT + 
            """
                WHERE v.user_id = %s AND v.restriction <> 'ban'
                ORDER BY reaction_count DESC,
                v.created_at DESC,
                v.id DESC
            """,
            (user_id,),
        )

    def get_vidio_id(self, video_id):
        return self._fetch_one(
            self.VIDEO_SELECT + "WHERE v.id = %s"
            (video_id,),
        )

    def get_admin_videos(self):
        return self._fetch_all(
            self.VIDEO_SELECT +
            "ORDER BY v.created_at DESC, v.id DESC"
        )
    def set_video_restriction(self, video_id, restriction):
        changed = self._execute(
            "UPDATE videos SET restriction = %s WHERE id = %s",
            (restriction, video_id)
        )