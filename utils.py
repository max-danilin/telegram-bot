from quiz import decode_question
import psycopg2
import os

HEROKU = os.getenv('HEROKU', False)

if HEROKU:
    DATABASE_URL = os.environ['DATABASE_URL']
else:
    from config import DATABASE_URL, DATABASE_NAME, DATABASE_PASSWORD, DATABASE_USER


class Database:
    """
    Class for connecting to PostgreSQL database.
    """
    def __init__(self, url: str, name: str = '', user: str = '', pwd: str = ''):
        """
        Initialize database
        :param url: db url
        :param name: db name
        :param user: dn username
        :param pwd: db username password
        """
        self.url = url
        self.name = name
        self.user = user
        self.pwd = pwd
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        Make connection.
        """
        if not HEROKU:
            self.conn = psycopg2.connect(dbname=self.name, user=self.user, password=self.pwd, host=self.url)
        else:
            self.conn = psycopg2.connect(self.url)
        self.cursor = self.conn.cursor()

    def close(self):
        """
        Close connection.
        """
        self.cursor.close()
        self.conn.close()


if HEROKU:
    database = Database(DATABASE_URL)
else:
    database = Database(url=DATABASE_URL, name=DATABASE_NAME, user=DATABASE_USER, pwd=DATABASE_PASSWORD)


class User:
    """
    Class for storing user's data.
    """
    def __init__(
            self, state, name, token=None, current_category=None, sub_category=None,
            current_difficulty='easy', current_question=None, correct_answers=0, incorrect_answers=0, id=None
    ):
        self.token = token
        self.state = state
        self.name = name
        self.current_category = current_category
        self.sub_category = sub_category
        self.current_difficulty = current_difficulty
        self.current_question = current_question
        self.correct_answers = correct_answers
        self.incorrect_answers = incorrect_answers
        self.id = id

    def __str__(self):
        return f'User with id {self.id}, token {self.token}, name {self.name}. Current category is ' \
               f'{self.current_category}, sub category - {self.sub_category}, difficulty - {self.current_difficulty}.' \
               f'Current state is {self.state}, number of correct/incorrect answers: {self.correct_answers}/' \
               f'{self.incorrect_answers}.'

    def to_json(self):
        """
        Prepares User object for converting to JSON format.
        :return: json serializable dictionary
        """
        question_json = self.current_question.json if self.current_question else None
        category = str(self.current_category) if self.current_category else None
        return {
            'token': self.token,
            'state': self.state,
            'name': self.name,
            'current_category': category,
            'current_difficulty': self.current_difficulty,
            'current_question': question_json,
            'sub_category': self.sub_category,
            'correct_answers': self.correct_answers,
            'incorrect_answers': self.incorrect_answers,
            'id': self.id
        }


def decode_user(user_json):
    """
    Decodes dictionary from JSON to User object.
    :param user_json: dict
    :return: User
    """
    q_json = user_json['current_question']
    user_json['current_question'] = decode_question(q_json)
    user_json['current_category'] = int(user_json['current_category']) if user_json['current_category'] else None
    return User(**user_json)


def parse_categories(all_cat, nested_cat):
    """
    Parse categories into main and sub ones.
    :param all_cat: all categories
    :param nested_cat: categories with sub categories
    :return: tuple(cat, subcat)
    """
    categories = []
    sub_categories = {key: [] for key in nested_cat}
    for category in all_cat:
        has_sub = False
        for name in nested_cat:
            if category['name'].lower().__contains__(name):
                if ':' in category['name']:
                    cleaned_sub = category['name'].split(':')[1][1:]
                else:
                    cleaned_sub = category['name']
                sub_categories[name].append(cleaned_sub)
                has_sub = True
        if not has_sub:
            categories.append(category['name'])
    for cat in nested_cat:
        categories.append(cat.capitalize())
    return categories, sub_categories


def get_category_id_by_name(name, all_cat):
    for item in all_cat:
        if name == item['name']:
            return item['id']