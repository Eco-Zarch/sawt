import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from inquirer import route_question
from helper import get_dbs
from api import RESPONSE_TYPE_DEPTH

MODEL = 'gpt-3.5-turbo-1106'

db_fc, db_cj, db_pdf, db_pc, db_news, voting_roll_df = get_dbs()

#get query from user input
query = input("Enter your query: ")

result= route_question(
    voting_roll_df,
    db_fc,
    db_cj,
    db_pdf,
    db_pc,
    db_news,
    query,
    RESPONSE_TYPE_DEPTH,
    k=10,
)

print(result)