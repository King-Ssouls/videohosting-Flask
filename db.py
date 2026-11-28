import psycopg
from psycopg.rows import dict_row
from config import Config


class Database:
    #общая реализация запроса на видео
    VIDEO_SELECT = """
        SELECT 
            v.*,
            u.nickname AS author_name,
            c.name AS category_name,
            COALESCE(r.likes_count, 0) AS likes_count,
            COALESCE(r.dislikes_count, 0) AS dislikes_count,
            COALESCE(r.likes_count, 0) + COALESCE(r.dislikes_count, 0) AS reaction_count,
            COALESCE(cm.comments_count, 0) AS comments_count
        FROM videos AS v
        JOIN users AS u ON u.id = v.user_id
        JOIN categories AS c ON c.id = v.category_id
        LEFT JOIN (
            SELECT 
                video_id,
                COUNT(*) FILTER (WHERE reaction_type = 'like') AS likes_count,
                COUNT(*) FILTER (WHERE reaction_type = 'dislike') AS dislikes_count
            FROM reactions
            GROUP BY video_id
        ) AS r ON r.video_id = v.id
        LEFT JOIN (
            SELECT 
                video_id,
                COUNT(*) AS comments_count
            FROM comments
            GROUP BY video_id
        ) AS cm ON cm.video_id = v.id
    """

    def __init__(self, db_params=None):
        if db_params is None:
            db_params = Config.DB_PARAMS

        self.db_params = dict(db_params)

    def get_db(self):
        return psycopg.connect(
            **self.db_params,
            row_factory=dict_row,
            connect_timeout=5
        )

    # служебные методы для сокращения запросов 
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
        user = self._fetch_one(
            """
                INSERT INTO users (nickname, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
            (nickname.strip(), email.strip().lower(), password_hash, role)
        )
        return user["id"]

    # функции для работы с user
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

    # функции дял работы с категориями
    def get_categories(self):
        return self._fetch_all(
            "SELECT id, name FROM categories ORDER BY id"
        )

    def get_categories_id(self, categories_id):
        return self._fetch_one(
            "SELECT id, name FROM categories WHERE id = %s",
            (categories_id,),
        )

    # функции для работы c видеороликов
    def create_video(self, user_id, category_id, title, file_name, description=""):
        video = self._fetch_one(
            """
                INSERT INTO videos (
                    user_id, category_id, title, file_name, description
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """,
            (user_id, category_id, title, file_name, description)
        )
        return video["id"]

    def get_latest_videos(self):
        return self._fetch_all(
            self.VIDEO_SELECT +
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
            self.VIDEO_SELECT + " WHERE v.id = %s",
            (video_id,),
        )

    def get_admin_videos(self):
        return self._fetch_all(
            self.VIDEO_SELECT +
            " ORDER BY v.created_at DESC, v.id DESC"
        )

    def set_video_restriction(self, video_id, restriction):
        changed = self._execute(
            "UPDATE videos SET restriction = %s WHERE id = %s",
            (restriction, video_id)
        )
        return changed > 0

    #aeyrwebb реакции связь 1 к 1
    def get_user_reaction(self, user_id, video_id):
        reaction = self._fetch_one(
            """
                SELECT reaction_type FROM reactions
                WHERE user_id = %s AND video_id = %s
            """,
            (user_id, video_id),
        )
        return reaction["reaction_type"] if reaction is not None else None

    def set_reaction(self, user_id, video_id, reaction_type):
        reaction = self._fetch_one(
            """
                INSERT INTO reactions (user_id, video_id, reaction_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, video_id)
                DO UPDATE SET reaction_type = EXCLUDED.reaction_type
                RETURNING id
            """,
            (user_id, video_id, reaction_type),
        )
        return reaction["id"]

    def delete_reaction(self, user_id, video_id):
        deleted_reaction = self._execute(
            "DELETE FROM reactions WHERE user_id = %s AND video_id = %s",
            (user_id, video_id),
        )
        return deleted_reaction > 0

    # функции под запросов коммы
    def created_comment(self, user_id, video_id, text):
        comment = self._fetch_one(
            """
                INSERT INTO comments (user_id, video_id, text)
                VALUES (%s, %s, %s)
                RETURNING id
            """,
            (user_id, video_id, text),
        )
        return comment["id"]

    def get_comment(self, video_id):
        return self._fetch_all(
            """
                SELECT c.*, u.nickname AS author_name
                FROM comments AS c
                JOIN users AS u ON u.id = c.user_id
                WHERE c.video_id = %s
                ORDER BY c.created_at DESC, c.id DESC
            """,
            (video_id,),
        )


if __name__ == "__main__":
    db = Database()
    categories = db.get_categories()
    print("коннект имеется")
    for category in categories:
        print(category["id"], category["name"])