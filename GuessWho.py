from flask import Flask, render_template, request
import random
import numpy as np
import mysql.connector
from mysql.connector import Error

def create_server_connection(host_name, user_name, user_password, database):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = host_name,
            user = user_name,
            passwd = user_password,
            database = database
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def get_DB_info(connection):
    cursor = connection.cursor()
    
    cursor.execute('SELECT idQuestions FROM questions')
    idQuestions = []
    for row in cursor:
        for field in row:
            idQuestions.append(field)

    cursor.execute('SELECT Question FROM questions')
    Questions = []
    for row in cursor:
        for field in row:
            Questions.append(field)
    return idQuestions, Questions

def calculate_probabilites(questions_so_far, answers_so_far):
    probabilities = []
    for character in characters:
        probabilities.append({
            'name': character['name'],
            'probability': calculate_character_probability(character, questions_so_far, answers_so_far)
        })
    return probabilities

def calculate_character_probability(character, questions_so_far, answers_so_far):
    P_character = 1 / len(characters)
    P_answers_given_character = 1
    P_answers_given_not_character = 1
    for question, answer in zip(questions_so_far, answers_so_far):
        P_answers_given_character *= max(
            1 - abs(answer - character_answer(character, question)), 0.01)

        P_answer_not_character = np.mean([1 - abs(answer - character_answer(not_character, question))
                                          for not_character in characters
                                          if not_character['name'] != character['name']])
        P_answers_given_not_character *= max(P_answer_not_character, 0.01)

    P_answers = P_character * P_answers_given_character + \
        (1 - P_character) * P_answers_given_not_character
    
    # Bayes Theorem
    P_character_given_answers = (
        P_answers_given_character * P_character) / P_answers
    return P_character_given_answers

def character_answer(character, question):
    if question in character['answers']:
        return character['answers'][question]
    return 0.5

app = Flask(__name__)

characters = [
    {'name': 'Jorge Valdivia',       'answers': {1: 0.75, 2: 1   , 3: 0, 4: 0.75, 5: 0, 6: 0   , 7: 0.25, 8: 0   , 9: 1    , 10: 1   }},
    {'name': 'Isaac Hernandez',      'answers': {1: 0.75, 2: 0.25, 3: 1, 4: 0   , 5: 1, 6: 0.25, 7: 0   , 8: 0.75, 9: 1    , 10: 0.75}},
    {'name': 'Gerardo Rocha',        'answers': {1: 0.75, 2: 0   , 3: 0, 4: 1   , 5: 0, 6: 0   , 7: 1   , 8: 1   , 9: 0    , 10: 0.75}},
    {'name': 'Johan "Lee" Garcia',   'answers': {1: 1   , 2: 1   , 3: 1, 4: 1   , 5: 0, 6: 0   , 7: 0.25, 8: 1   , 9: 0.75 , 10: 1   }},
    {'name': 'Alejandro García',     'answers': {1: 1   , 2: 0   , 3: 0, 4: 0.25, 5: 0, 6: 1   , 7: 1   , 8: 0   , 9: 0.75 , 10: 0.75}},
    {'name': 'Hector Figueroa',      'answers': {1: 1   , 2: 0   , 3: 0, 4: 0.25, 5: 0, 6: 0.25, 7: 1   , 8: 0.25, 9: 0.75 , 10: 0.75}},
    {'name': 'Paulo Salvatore',      'answers': {1: 0.75, 2: 0   , 3: 1, 4: 0   , 5: 0, 6: 0.25, 7: 0.75, 8: 0.25, 9: 0.75 , 10: 1   }},
    {'name': 'Jordan Ventura',       'answers': {1: 0.75, 2: 0.75, 3: 0, 4: 0   , 5: 1, 6: 0.25, 7: 0   , 8: 0.25, 9: 0    , 10: 0   }},
]

connection = create_server_connection("localhost", "root", "hejefica", "guesswho")
idQuestions, Questions = get_DB_info(connection)
questions_so_far = []
answers_so_far = []

@app.route('/')
def index():
    global questions_so_far, answers_so_far

    question = request.args.get('question')
    answer = request.args.get('answer')
    if question and answer:
        questions_so_far.append(int(question))
        answers_so_far.append(float(answer))
    probabilities = calculate_probabilites(questions_so_far, answers_so_far)

    questions_left = list(set(idQuestions) - set(questions_so_far))
    if len(questions_left) == 0:
        result = sorted(
            probabilities, key = lambda p: p['probability'], reverse = True)[0]
        return render_template('index.html', result = result['name'])
    else:
        next_question = random.choice(questions_left)
        return render_template('index.html', question = next_question, question_text = Questions[next_question - 1])

if __name__ == '__main__':
    app.run()