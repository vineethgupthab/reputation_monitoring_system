import os
import pickle
import shutil
import pandas as pd
from tqdm import tqdm
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts.few_shot import FewShotPromptTemplate

def create_sentiment_classification_prompt(content, topic):
    """Create a sentiment classification prompt based on the given topic.

    Args:
        content (str): The content of the news article.
        topic (str): The topic for which the prompt is created.

    Returns:
        ChatPromptTemplate: The generated prompt template.
    """
    sentiment_classification_template = (
        f'This is the news article {content} related to {topic}. '
        'Strictly restrict and clearly focus on content related to {topic}. '
        'Return either Positive or Negative or Neutral according to the '
        f'content sentiment towards the {topic}. If the content is not '
        f'related to the {topic} at all then return Not-related'
    )
    sentiment_prompt = ChatPromptTemplate.from_template(sentiment_classification_template)
    return sentiment_prompt


def create_few_shot_sentiment_classification_prompt(examples):
    """
    Create a prompt template for few-shot sentiment classification based on given examples.

    Parameters:
    examples (list): A list of tuples where each tuple contains a question and its corresponding answer.

    Returns:
    PromptTemplate: A prompt template for few-shot sentiment classification.
    """
    example_prompt = PromptTemplate(
    input_variables=["Question", "answer"], template="Question: {question}\n{answer}")
    prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="""This is the news article {content} related to {topic}. Return either Positive or Negative or Neutral according to the content sentiment towards the {topic}. 
    If the content is not related to the topic at all then return Not-related""",
    input_variables=["content","topic"])
    return prompt


def create_summarization_prompt(content, topic):
    """Create a summarization prompt based on the given content and topic.

    Args:
        content (str): The content of the news article.
        topic (str): The topic for which the summary is created.

    Returns:
        ChatPromptTemplate: The generated prompt template.
    """
    summarization_template = (
        f'This is the news article content {content}. '
        'Strictly restrict and Summarize the content of this news article in 50 words '
        f'such that whole important content related to the {topic} is covered within these 50 words. '
        'Strictly restrict to this content only. Please avoid anything that is not related to this content. '
        f'If the content is not related to the {topic}, just return Not-related content.'
    )
    summarization_prompt = ChatPromptTemplate.from_template(summarization_template)
    return summarization_prompt


if __name__ == '__main__':
    with open('gemini_api_key.pickle', 'rb') as handle:
        gemini_api_key = pickle.load(handle)
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro",
                                 google_api_key=gemini_api_key,
                                 temperature=0, top_p=1)
    output_parser = StrOutputParser()
    topics = []
    
    with open('topics.txt', 'r') as f:
        for line in f:
            topics.append(line.strip())
    
    data = pd.read_csv('/Users/vineethguptha/github/reputation_monitoring_system/few_shots_sentiments.csv')
    examples = [{'question':row['content'], 'answer':row['label']} for index, row in data.iterrows()]
    
    for topic in topics:
        try:
            data = pd.read_csv(f'intermediate/{topic}.csv')
        except FileNotFoundError as e:
            print('No new data found for', topic)
            break
        texts = data['content'].values
        sentiments = []
        
        for i in tqdm(range(len(texts))):
            try:
                # sentiment_prompt = create_sentiment_classification_prompt(texts[i], topic)
                # sentiment_chain = sentiment_prompt | llm | output_parser
                prompt = create_few_shot_sentiment_classification_prompt(examples)
                sentiment_chain = prompt | llm | output_parser
                sentiments.append(sentiment_chain.invoke({"topic": topic, "content": texts[i]}))
            except:
                sentiments.append('Neutral')
        
        data['text sentiment'] = sentiments

        summaries = []
        for ind, row in tqdm(data.iterrows()):
            try:
                summarization_prompt = create_summarization_prompt(row['content'], topic)
                summarizer_chain = summarization_prompt | llm | output_parser
                summaries.append(summarizer_chain.invoke({"topic": topic, "content": row['content']}))
            except Exception as e:
                summaries.append('Not-related content')
        
        data['summaries'] = summaries

        # Check if the old data file exists
        old_file_path = f'results/{topic}.csv'
        if os.path.exists(old_file_path):
            old_data = pd.read_csv(old_file_path)
            
            data = pd.concat([old_data, data])
        data = data.drop_duplicates()
        data.to_csv(old_file_path, index=False)
        print(f'Data and results for {topic} are saved')
        os.remove(f'intermediate/{topic}.csv')
