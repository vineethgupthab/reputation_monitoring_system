import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta, date
import plotly.graph_objects as go
import io
import requests

# Set page configuration
st.set_page_config(layout="wide", page_title="Analysis Dashboard")

# Define the path for the datasets
dataset_path = 'results/'

# Define topics and corresponding file names
# Because keys are defined kind of inconsistently
# lower case key definitions exist
topics_dict = {
    'Fannie Mae': 'Fannie Mae.csv',
    'Federal Home Loan Bank of San Francisco': 
        'Federal Home Loan Bank of San Francisco.csv',
    'First Republic Bank': 'First Republic Bank.csv'
}


bulletpoints = pd.read_csv(f'{dataset_path}bullets.csv')

# Function to load and sort data
def load_data(topic_name):
    df = pd.read_csv(dataset_path + topics_dict[topic_name])
    df = df.sort_values(by='publish_date', ascending=False)
    df = df[df['summaries'] != 'Not-related content']
    df = df[df['summaries'] != 'Not-related content.']
    df['publish_date'] = pd.to_datetime(df['publish_date'])
    return df


def load_aggregated_data(topic_name, days):
    '''df = pd.read_csv(dataset_path + topics_dict[topic_name])
    df['publish_date'] = pd.to_datetime(df['publish_date']).dt.date'''
    df = load_data(topic_name)

    # Aggregate data by day
    daily_summary = df.groupby('publish_date').agg({
        'default_sentiment': 'mean',  # Average sentiment per day
        'title': 'count'  # Count of entries per day, assuming 'title' as a proxy for entries
    }).rename(columns={'default_sentiment': 'average_sentiment', 'title': 'count_per_day'})

    # Create a date range for the last 'days' days, normalized to dates
    end_date = pd.to_datetime("today").normalize()
    start_date = end_date - pd.Timedelta(days=days - 1)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D').date

    # Reindex the DataFrame to include all days in the last 'days' days, filling missing days with NaN
    full_summary = daily_summary.reindex(date_range).fillna({
        'average_sentiment': 0,  # Fill missing sentiment averages with 0
        'count_per_day': 0       # Fill missing counts with 0
    })

    return full_summary
st.markdown("<h1 style='text-align: center; color: #005A8D;'>Member Analysis</h1>", unsafe_allow_html=True)

# Tab names
tab_names = ['Analysis', 'News Summaries']

# Select tab
selected_tab = st.sidebar.radio("Select Tab", tab_names)

if selected_tab=='Analysis':

    col1, col2 = st.columns(2)
    with col1:
        selected_topic = st.selectbox('Select the Member', bulletpoints['topic'].unique())
    with col2:
        selected_time_period = st.selectbox('Select time period', ['Week', 'Month', 'Quarter'])
        timeframe_days = {'Week': 7, 'Month': 30, 'Quarter': 90}
        days = timeframe_days[selected_time_period]

    st.markdown("---", unsafe_allow_html=True)  # Horizontal line

    col1, col2, col3 = st.columns(3)

    filtered_data = load_aggregated_data(selected_topic, days)

    data = pd.read_csv(f'results/{selected_topic}.csv')
    data = data[data['summaries'] != 'Not-related content.']
    data = data[data['summaries'] != 'Not-related content']

    data['publish_date'] = pd.to_datetime(data['published date']).dt.date
    # Sort data by publish_date
    data.sort_values('publish_date', ascending=False, inplace=True)
    today = date.today()
    date = today - timedelta(days=days)
    selected_data = data[(data['publish_date'] > date)]

    # First section: Number of articles over time and displaying bullet points for positive sentences
    with col1:
        # Plotting the number of articles
        article_count_plot = px.line(filtered_data, y='count_per_day', labels={'index': 'Date', 'count_per_day': 'Article Count'},
                                        title=f'Number of Articles per {selected_time_period}')
        article_count_plot.update_layout(xaxis_title='Date', yaxis_title='Number of Articles', plot_bgcolor='#F4F6F9', paper_bgcolor='#F4F6F9')
        article_count_plot.update_layout(title={'x':0.5, 'xanchor': 'center'})
        st.plotly_chart(article_count_plot, use_container_width=True)

        # Display bullet points for positive news
        topic_bullets = bulletpoints[(bulletpoints['topic'] == selected_topic) & (bulletpoints['timeframe'] == f'{selected_time_period}ly')]
        #print(topic_bullets)
        positive_sentences = [sentence.strip('- ').strip() for sentence in topic_bullets['positive'].iloc[0].split('\n') if sentence]
        st.subheader('Positive News')
        st.markdown("<ul style='list-style-type: disc; padding-left: 20px; text-align: center;'>", unsafe_allow_html=True)
        for sentence in positive_sentences:
            st.markdown(f"<li style='color: #006E8D;'>{sentence}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    # Second section: Sentiment over time and displaying bullet points for negative sentences
    with col2:
        # Plotting sentiment over time
        sentiment_plot = px.line(filtered_data, y='average_sentiment', labels={'index': 'Date', 'average_sentiment': 'Average Sentiment'},
                                    title=f'Sentiment over {selected_time_period}')
        sentiment_plot.update_layout(xaxis_title='Date', yaxis_title='Sentiment Score', plot_bgcolor='#F4F6F9', paper_bgcolor='#F4F6F9')
        sentiment_plot.update_layout(title={'x':0.5, 'xanchor': 'center'})
        sentiment_plot.update_traces(line_color='#FF5733')
        st.plotly_chart(sentiment_plot, use_container_width=True)

        # Display bullet points for negative news
        try:
            negative_sentences = [sentence.strip('- ').strip() for sentence in topic_bullets['negative'].iloc[0].split('\n') if sentence]
        except:
            negative_sentences = ['']
        st.subheader('Negative News')
        st.markdown("<ul style='list-style-type: disc; padding_left: 20px; text-align: center;'>", unsafe_allow_html=True)
        for sentence in negative_sentences:
            st.markdown(f"<li style='color: #FF5733;'>{sentence}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    # Optionally, you can add additional visualizations or data summaries in col3 or elsewhere as needed



    # Third section: Image, today's sentiment, number of articles today
    articles_in_time = filtered_data['count_per_day'].sum()

    # Third section: Image, today's sentiment, number of articles today
    articles_in_time = filtered_data['count_per_day'].sum()

    with col3:
        # Calculate the average sentiment
        average_sentiment = filtered_data['average_sentiment'].mean() * 100

        # Determine sentiment text
        sentiment_text = ""
        if -10 <= average_sentiment <= 10:
            sentiment_text = "Neutral"
        elif -30 <= average_sentiment < -10:
            sentiment_text = "Slightly Negative"
        elif -60 <= average_sentiment < -30:
            sentiment_text = "Moderately Negative"
        elif average_sentiment < -60:
            sentiment_text = "Very Negative"
        elif 10 < average_sentiment <= 30:
            sentiment_text = "Slightly Positive"
        elif 30 < average_sentiment <= 60:
            sentiment_text = "Moderately Positive"
        elif average_sentiment > 60:
            sentiment_text = "Very Positive"

        # Convert average sentiment to percentage and add percentage sign
        average_sentiment_percentage = f"{average_sentiment:.2f}%"

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=average_sentiment,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Average Sentiment"},
            gauge={
                'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': 'rgb(128, 122, 0)', 'thickness': 0.75},
                'bgcolor': "#F4F6F9",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-100, -50], 'color': 'rgb(255, 0, 0)'},
                    {'range': [-50, 50], 'color': 'rgb(255, 255, 255)'},
                    {'range': [50, 100], 'color': 'rgb(60, 255, 0)'}
                ],
            }
        ))

        # Add percentage sign and sentiment text
        fig.update_layout(
            annotations=[
                dict(
                    text=f"{sentiment_text}",
                    x=0.5,
                    y=0.5,
                    font=dict(size=24),
                    showarrow=False,
                    align="center"
                )
            ]
        )

        fig.update_layout(plot_bgcolor="#F0F2F6")  # Set background color for the graph
        fig.update_layout(paper_bgcolor="#F0F2F6")  # Set background color for the plot area

        # Define image_path with a default image
        default_image_path = 'logos/Default-Logo.png'  # Adjust to a valid default image path
        image_path = {
            'Federal Home Loan Bank of San Francisco': 'logos/Federal-Home-Loan-Bank-Logo.png',
            'Fannie Mae': 'logos/Fannie-Mae-Logo.png',
            'First Republic Bank': 'logos/First-Republic-Bank-Logo.png',
        }.get(selected_topic, default_image_path)

        try:
            image = Image.open(image_path)
            st.image(image, use_column_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

        st.markdown(f'<p style="color: #005A8D; font-size: 18px; text-align: center ; " > Number of news articles released this {selected_time_period}: {len(selected_data)} </p>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

elif selected_tab=='News Summaries':

    col1, col2 = st.columns(2)
    with col1:
        selected_topic = st.selectbox('Select the Member', bulletpoints['topic'].unique())
    with col2:
        selected_time_period = st.selectbox('Select time period', ['Week', 'Month', 'Quarter'])
        timeframe_days = {'Week': 7, 'Month': 30, 'Quarter': 90}
        days = timeframe_days[selected_time_period]

    st.markdown("---", unsafe_allow_html=True)  # Horizontal line

    col1, col2, col3 = st.columns(3)

    data = pd.read_csv(f'results/{selected_topic}.csv')
    data = data[data['summaries'] != 'Not-related content.']
    data = data[data['summaries'] != 'Not-related content']
    
    data['publish_date'] = pd.to_datetime(data['published date']).dt.date
    # Sort data by publish_date
    data.sort_values('publish_date', ascending=False, inplace=True)
    today = date.today()
    date = today - timedelta(days=days)
    filtered_data = data[(data['publish_date'] > date)]

    # First section: Number of articles over time and displaying bullet points for positive sentences
    with col1:
        # Display bullet points for positive news
        # topic_bullets = bulletpoints[(bulletpoints['topic'] == selected_topic) & (bulletpoints['timeframe'] == f'{selected_time_period.lower()}ly')]
        # positive_sentences = [sentence.strip('- ').strip() for sentence in topic_bullets['positive'].iloc[0].split('\n') if sentence]
        positive_data = filtered_data[filtered_data['text sentiment']=='Positive']
        positive_sentences = positive_data['summaries'].values
        st.subheader('Positive News')
        st.markdown("<ul style='list-style-type: disc; padding-left: 20px; text-align: center;'>", unsafe_allow_html=True)
        for ind, row in positive_data.iterrows():
            st.markdown(f"<li style='color: #006E8D;'>{row['summaries']} - <a href={row['url']}>{row['publisher']} published on {row['publish_date']}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)

    # Second section: Sentiment over time and displaying bullet points for negative sentences
    with col2:

        # Display bullet points for negative news
        # negative_sentences = [sentence.strip('- ').strip() for sentence in topic_bullets['negative'].iloc[0].split('\n') if sentence]
        negative_data = filtered_data[filtered_data['text sentiment']=='Negative']
        negative_sentences = negative_data['summaries'].values
        st.subheader('Negative News')
        st.markdown("<ul style='list-style-type: disc; padding_left: 20px; text-align: center;'>", unsafe_allow_html=True)
        for ind, row in negative_data.iterrows():
            st.markdown(f"<li style='color: #FF5733;'>{row['summaries']} - <a href={row['url']}>{row['publisher']} published on {row['publish_date']}</li>", unsafe_allow_html=True)
        st.markdown("</ul>", unsafe_allow_html=True)
    # Third section: Image, today's sentiment, number of articles today
    pos_articles_in_time = len(positive_data)
    neg_articles_in_time = len(negative_data)

    with col3:
        
        # Define image_path with a default image
        default_image_path = 'logos/Default-Logo.png'  # Adjust to a valid default image path
        image_path = {
            'Federal Home Loan Bank of San Francisco': 'logos/Federal-Home-Loan-Bank-Logo.png',
            'Fannie Mae': 'logos/Fannie-Mae-Logo.png',
            'First Republic Bank': 'logos/First-Republic-Bank-Logo.png',
        }.get(selected_topic, default_image_path)

        try:
            image = Image.open(image_path)
            st.image(image, use_column_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")

        st.markdown(f'<p style="color: #005A8D; font-size: 18px; text-align: center ; " > Number of positive news articles released this {selected_time_period}: {pos_articles_in_time} </p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #005A8D; font-size: 18px; text-align: center ; " > Number of negative articles released this {selected_time_period}: {neg_articles_in_time} </p>', unsafe_allow_html=True)
