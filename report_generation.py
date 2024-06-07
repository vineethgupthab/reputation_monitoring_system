import pandas as pd
from tqdm import tqdm
import os
import time
from langchain_core.documents import Document
from datetime import date, timedelta
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import pickle

def create_positive_summarization_prompt(contents, topic):
    """ Create a summarization prompt based on the given content and topic.
    Args:
        content (str): The content of the news article.
        topic (str): The topic for which the summary is created.
    Returns:
        ChatPromptTemplate: The generated prompt template.
    """
    summarization_template = """These are the news articles {contents} related to the topic {topic} and are positive towards the {topic}. Strictly restrict the knowledge to this content only and select only unique positive crucial information from all these articles that could increase the reputation of {topic} in public and return 3 unique important detailed bullet points that has most important information, if you could not get 3 bullet points, no problem pull as many as you can""".format(contents=contents, topic=topic)
    summarization_prompt = ChatPromptTemplate.from_template(summarization_template)
    return summarization_prompt

def create_negative_summarization_prompt(contents, topic):
    """ Create a summarization prompt based on the given content and topic.
    Args:
        content (str): The content of the news article.
        topic (str): The topic for which the summary is created.
    Returns:
        ChatPromptTemplate: The generated prompt template.
    """
    summarization_template = """These are the news articles {contents} related to the topic {topic} and are negative towards the {topic}.  Strictly restrict the knowledge to this content only and select only unique negative crucial information from all these articles that could decrease the reputation of {topic} in public and return 3 unique detailed important bullet points that has most important information, if you could not get 3 bullet points, no problem pull as many as you can""".format(contents=contents, topic=topic)
    summarization_prompt = ChatPromptTemplate.from_template(summarization_template)
    return summarization_prompt

if __name__ == '__main__':
    # Load gemini API key
    with open('/Users/vineethguptha/fhlbsf/gemini_api_key.pickle', 'rb') as handle:
        gemini_api_key = pickle.load(handle)
    llm = ChatGoogleGenerativeAI(model="gemini-pro",
                                    google_api_key=gemini_api_key,
                                    temperature=0, top_p=0.1)
    output_parser = StrOutputParser()

    result = pd.DataFrame(columns=['Topic','Timeframe','Positive','Negative'])

    # Define quarter, month, and week dates
    today = date.today()
    quarter_date = today - timedelta(days=120)
    month_date = today - timedelta(days=30)
    week_date = today - timedelta(days=7)
    date_filters = {"Weekly": week_date, "Monthly": month_date, "Quarterly": quarter_date}

    # Read topics from file
    with open('topics.txt', 'r') as f:
        topics = [line.strip() for line in f]
    result = pd.DataFrame(columns=['topic','timeframe','positive','negative'])
    for topic in tqdm(topics):
        data = pd.read_csv(f'results/{topic}.csv')
        # Filter out unrelated content
        data = data[data['summaries'] != 'Not-related content.']
        data = data[data['summaries'] != 'Not-related content']
        data.reset_index(inplace=True)
        # Convert publish_date to datetime
        data['publish_date'] = pd.to_datetime(data['published date']).dt.date
        # Sort data by publish_date
        data.sort_values('publish_date', ascending=False, inplace=True)
        print(data)

        for key, date in date_filters.items():
            filtered_data_pos = data[(data['publish_date'] > date)&(data['text sentiment']=='Positive')]

            # negative data
            filtered_data_neg = data[(data['publish_date'] > date)&(data['text sentiment']=='Negative')]

            print(topic, key, filtered_data_pos.shape, filtered_data_neg.shape)

            contents = '----'.join(filtered_data_pos['summaries'].values)
            urls = '----'.join(filtered_data_pos['url'].values)
            summarization_prompt = create_positive_summarization_prompt(contents, topic)
            summarizer_chain = summarization_prompt | llm | output_parser
            pos_summaries = summarizer_chain.invoke(
                {"topic": topic, "contents": contents})

            # print(pos_summaries, '\n\n')

            contents = '----'.join(filtered_data_neg['summaries'].values)
            urls = '----'.join(filtered_data_neg['url'].values)
            if len(filtered_data_neg['summaries'].values)>0:
                summarization_prompt = create_negative_summarization_prompt(contents, topic)
                summarizer_chain = summarization_prompt | llm | output_parser
                neg_summaries = summarizer_chain.invoke(
                    {"topic": topic, "contents": contents})
            else:
                neg_summaries=''

            # print(neg_summaries)

            new_row = {'topic':topic, 'timeframe':key, 'positive':pos_summaries, 'negative':neg_summaries}
            #print(pos_summaries, neg_summaries)
            result.loc[len(result)] = new_row
    result.to_csv('/Users/vineethguptha/github/reputation_monitoring_system/results/bullets.csv', index=False)