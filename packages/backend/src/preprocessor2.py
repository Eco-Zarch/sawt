import logging 
import os
from langchain_community.document_loaders.json_loader import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from langchain.prompts import PromptTemplate
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAI
from pathlib import Path
import shutil
from langchain_experimental.text_splitter import SemanticChunker
from langchain.docstore.document import Document
import sys
import pandas as pd
import openai


logger = logging.getLogger(__name__)
dir = Path(__file__).parent.absolute()



def create_embeddings():
    llm = OpenAI()

    base_embeddings = OpenAIEmbeddings()

    general_prompt_template = """
    As an AI assistant, your role is to provide concise, balanced summaries from the transcripts of New Orleans City Council meetings in response to the user's query "{user_query}". Your response should not exceed one paragraph in length. If the available information from the transcripts is insufficient to accurately summarize the issue, respond with 'Insufficient information available.' If the user's query extends beyond the scope of information contained in the transcripts, state 'I don't know.'
    Answer:"""

    in_depth_prompt_template = """
    As an AI assistant, use the New Orleans City Council transcript data that you were trained on to provide an in-depth and balanced response to the following query: "{user_query}" 
    Answer:"""

    general_prompt = PromptTemplate(
        input_variables=["user_query"], template=general_prompt_template
    )
    in_depth_prompt = PromptTemplate(
        input_variables=["user_query"], template=in_depth_prompt_template
    )

    # llm_chain_general = LLMChain(llm=llm, prompt=general_prompt)
    # llm_chain_in_depth = LLMChain(llm=llm, prompt=in_depth_prompt)

    # general_embeddings = HypotheticalDocumentEmbedder(
    #     llm_chain=llm_chain_general,
    #     base_embeddings=base_embeddings,
    # )

    # in_depth_embeddings = HypotheticalDocumentEmbedder(
    #     llm_chain=llm_chain_in_depth, base_embeddings=base_embeddings
    # )

    return base_embeddings, base_embeddings


def metadata_func_minutes_and_agendas(record: dict, metadata: dict) -> dict:
    metadata["title"] = record.get("title")
    metadata["page_number"] = record.get("page_number")
    metadata["publish_date"] = record.get("publish_date")
    return metadata


def create_db_from_minutes_and_agendas(doc_directory):
    logger.info("Creating database from minutes...")
    all_docs = []
    for doc_file in os.listdir(doc_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(doc_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_func_minutes_and_agendas,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())
        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                print(
                    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                )
                all_docs.append(new_doc)
    logger.info("Finished database from minutes...")
    return all_docs


def metadata_news(record: dict, metadata: dict) -> dict:
    metadata["url"] = record.get("url")
    metadata["title"] = record.get("title")
    return metadata


def create_db_from_news_transcripts(news_json_directory):
    logger.info("Creating database from CJ transcripts...")
    all_docs = []
    for doc_file in os.listdir(news_json_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(news_json_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_news,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())
        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                print(
                    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                )
                all_docs.append(new_doc)
    logger.info("Finished database from news transcripts...")
    return all_docs


def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["timestamp"] = record.get("timestamp")
    metadata["url"] = record.get("url")
    metadata["title"] = record.get("title")
    metadata["publish_date"] = record.get("publish_date")

    return metadata


def create_db_from_cj_transcripts(cj_json_directory):
    logger.info("Creating database from CJ transcripts...")
    all_docs = []
    for doc_file in os.listdir(cj_json_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(cj_json_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_func,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())
        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                print(
                    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                )
                all_docs.append(new_doc)

    logger.info("Finished database from CJ transcripts...")
    return all_docs


def create_db_from_fc_transcripts(fc_json_directory):
    logger.info("Creating database from FC transcripts...")
    all_docs = []
    for doc_file in os.listdir(fc_json_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(fc_json_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_func,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())
        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                print(
                    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                )
                all_docs.append(new_doc)
    logger.info("Finished database from news transcripts...")  # change news to fc?
    return all_docs


# test transcript function


def create_db_from_test_transcripts(
    test_json_directory
):  # have this just work for the new files, keep date name, and delete after
    logger.info("Creating database from test transcripts...")
    all_docs = []
    print("Print CD:", os.getcwd()) # edit so that if nothing is on 3, this step is skipped

    # path_for_test_directory = f"packages/backend/{test_json_directory}"
    
    for doc_file in os.listdir(test_json_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(test_json_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_func,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())

        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)  ####
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                # print(
                #    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                # )
                all_docs.append(new_doc)
    logger.info("Finished database from test transcripts...")
    return all_docs


def create_db_from_public_comments(pc_json_directory):
    logger.info("Creating database from FC transcripts...")
    all_docs = []
    for doc_file in os.listdir(pc_json_directory):
        if not doc_file.endswith(".json"):
            continue
        doc_path = os.path.join(pc_json_directory, doc_file)
        loader = JSONLoader(
            file_path=doc_path,
            jq_schema=".messages[]",
            content_key="page_content",
            metadata_func=metadata_func,
        )

        data = loader.load()
        text_splitter = SemanticChunker(OpenAIEmbeddings())
        for doc in data:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                print(
                    f"Content: {new_doc.page_content}\nMetadata: {new_doc.metadata}\n"
                )
                all_docs.append(new_doc)
    logger.info("Finished database from Public Comments...")
    return all_docs


def create_vector_dbs(
    # fc_json_directory,
    # cj_json_directory,
    # doc_directory,
    # pc_directory,
    # news_directory,
    test_json_directory,
    in_depth_embeddings,
    df,
    LOG_FILE,
):
    # Create databases from transcripts and documents
    # fc_video_docs = create_db_from_fc_transcripts(fc_json_directory)
    # cj_video_docs = create_db_from_cj_transcripts(cj_json_directory)
    # pdf_docs = create_db_from_minutes_and_agendas(doc_directory)
    # pc_docs = create_db_from_public_comments(pc_directory)
    # news_docs = create_db_from_news_transcripts(news_directory)
    test_video_docs = create_db_from_test_transcripts(test_json_directory)

    # Function to create, save, and copy FAISS index
    def create_save_and_copy_faiss(docs, embeddings, doc_type, df, LOG_FILE):
        # Create FAISS index
        #db = FAISS.from_documents(docs, embeddings)  #### change this to add?
        # next time you call add documents it will use the same embeddings so you dont have to pass them in again
        
        # TRY THIS 
        # Path where FAISS index is saved
        faiss_path = "packages/backend/src/cache/faiss_index_in_depth_test"
        
        # Check if a FAISS index already exists at that path
        if os.path.exists(os.path.join(faiss_path, "index.faiss")):
            # Load existing FAISS index
            db = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)   
            # Add new documents 
            db.add_documents(docs)                          
            print("Added new documents to existing FAISS index.")
        else:
            # Create a new FAISS vector index using the documents
            db = FAISS.from_documents(docs, embeddings)     
            print("Created new FAISS index."),

        cache_dir = dir.joinpath("cache")

        # Save locally
        local_save_dir = cache_dir.joinpath(f"faiss_index_in_depth_{doc_type}")
        db.save_local(local_save_dir)
        logger.info(f"Local FAISS index for {doc_type} saved to {local_save_dir}")

        state_3_list = df[df["state"] == 3].to_dict(orient="records")
        for meeting in state_3_list:
            meeting_id = meeting["meeting_id"]
            df.loc[df["meeting_id"] == meeting_id, "state"] = 4
            df.to_json(LOG_FILE, orient="records", indent=4)
            print(f"DF updated to state 4: {meeting_id}")

        # put this back later

        # Copy to Google Cloud directory
        #  cloud_dir = dir.parent.parent.joinpath(
        #     f"googlecloud/functions/getanswer/cache/faiss_index_in_depth_{doc_type}"
        #  )
        #  shutil.copytree(local_save_dir, cloud_dir, dirs_exist_ok=True)
        # logger.info(
        #     f"FAISS index for {doc_type} copied to Google Cloud directory: {cloud_dir}"
        #   )

        df.to_json(LOG_FILE, orient="records", indent=4)
        return db, df

    # Creating, saving, and copying FAISS indices for each document type
    # faiss_fc = create_save_and_copy_faiss(fc_video_docs, in_depth_embeddings, "fc")
    # faiss_cj = create_save_and_copy_faiss(cj_video_docs, in_depth_embeddings, "cj")
    # faiss_pdf = create_save_and_copy_faiss(pdf_docs, in_depth_embeddings, "pdf")
    # faiss_pc = create_save_and_copy_faiss(pc_docs, in_depth_embeddings, "pc")
    # faiss_news = create_save_and_copy_faiss(news_docs, in_depth_embeddings, "news")
    # df = pd.read_json(LOG_FILE)
    faiss_test, df = create_save_and_copy_faiss(
        test_video_docs, in_depth_embeddings, "test", df, LOG_FILE
    )
    df.to_json(LOG_FILE, orient="records", indent=4)

    # Return the FAISS indices
    # return faiss_fc, faiss_cj, faiss_pdf, faiss_pc, faiss_news
    return faiss_test, df
