from quiz import decode_question


class User:
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

    def to_json(self):
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
    q_json = user_json['current_question']
    user_json['current_question'] = decode_question(q_json)
    user_json['current_category'] = int(user_json['current_category']) if user_json['current_category'] else None
    return User(**user_json)


def parse_categories(all_cat, nested_cat):
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