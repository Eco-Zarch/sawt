import logging
import os
import sys
from dotenv import find_dotenv, load_dotenv

from packages.backend.src.preprocessor2 import create_vector_dbs, create_embeddings

load_dotenv(find_dotenv())



logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


def main(df, LOG_FILE):
    load_dotenv(find_dotenv())
    print("Env file path found:", find_dotenv())
    '''
    pdf_directory = "minutes_agendas_directory"
    cj_json_directory = "json_cj_directory"
    fc_json_directory = "json_fc_directory"
    pc_json_directory = "json_public_comment_directory"
    news_json_directory = "news_directory"
    '''
    test_json_directory = "packages/backend/src/json_test_directory" #test 
    print(f"Preprocessing videos, agendas, and minutes to generate a cache.")
    general_embeddings, in_depth_embeddings = create_embeddings()

    # create_db_from_fc_youtube_urls(FC_INPUT_VIDEO_URLS)
    create_vector_dbs(
        #fc_json_directory,
        #cj_json_directory,
        #pdf_directory,
       # pc_json_directory,
        #news_json_directory,
        test_json_directory,
        in_depth_embeddings, 
        df, 
        LOG_FILE
    )
    return df


#if __name__ == "__main__":
    #print('In main!')
    #main(df, LOG_FILE)
