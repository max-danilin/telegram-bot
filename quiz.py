import requests


class Question:  # TODO mb try dataclass
    def __init__(self, category, type, difficulty, question, correct_answer, incorrect_answers):
        self.category = category
        self.type = type
        self.difficulty = difficulty
        self.question = question
        self.correct_answer = correct_answer
        self.incorrect_answers = incorrect_answers
        self.json = None


def decode_question(q_json):
    if q_json is not None:
        q = Question(**q_json)
        q.json = q_json
        return q
    else:
        return None


class QuizAPIException(Exception):
    pass


class GetTokenException(Exception):
    pass


def get_token():
    token_get_url = 'https://opentdb.com/api_token.php?command=request'
    response_token = requests.get(token_get_url)
    if response_token.ok:
        token = response_token.json()['token']
        return token
    else:
        raise QuizAPIException(f"Произошла ошибка API, код ответа {response_token['response_code']}")


def get_categories():
    categories_url = 'https://opentdb.com/api_category.php'
    response_category = requests.get(categories_url)
    if response_category.ok:
        categories = response_category.json()['trivia_categories']
        return categories
    else:
        raise QuizAPIException(f"Произошла ошибка API, код ответа {response_category['response_code']}")


def ask_question(token, category, difficulty):
    base_url = 'https://opentdb.com/api.php?amount=1&category=' + category + '&difficulty=' + difficulty +\
               '&token=' + token

    response = requests.get(base_url).json()
    if response['response_code'] == 0:
        question = Question(**response['results'][0])
        question.json = response['results'][0]
        return question
    elif response['response_code'] == 3 or response['response_code'] == 4:
        raise GetTokenException('Необходимо обновить токен.')
    else:
        raise QuizAPIException(f"Произошла ошибка API, код ответа {response['response_code']}")

