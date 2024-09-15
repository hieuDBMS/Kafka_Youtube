import json
import random
import time
import os
import pytz
import pandas as pd
from multiprocessing import Process
from confluent_kafka import Producer
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from Youtube_project2.queries import *
from Youtube_project2.mysql_connector import *

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Build the YouTube API client
youtube = build('youtube', 'v3', developerKey=API_KEY)


def convert_datetime(iso_datetime_str):
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    try:
        # Parse the ISO 8601 datetime string, including handling the 'Z' suffix
        dt = datetime.fromisoformat(iso_datetime_str.replace('Z', '+00:00'))
        # Convert to Vietnam/Ho_Chi_Minh timezone
        dt_vietnam = dt.astimezone(vietnam_tz)
        # Convert to MySQL format
        return int(dt_vietnam.timestamp())
    except ValueError:
        # Return a default value or handle the error if parsing fails
        return int(datetime.now(vietnam_tz).timestamp())


def get_detail_videos(video_ids):
    ho_chi_minh_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    all_video_details = []

    response = youtube.videos().list(
        part='statistics,snippet,contentDetails',
        id=','.join(video_ids)
    ).execute()

    for item in response['items']:
        video_id = item['id']
        video_details = item['statistics']
        video_snippet = item['snippet']
        video_contentDetails = item['contentDetails']
        row = (
            video_id,
            video_snippet['channelId'],
            video_snippet['title'],
            video_contentDetails['duration'],
            video_details['viewCount'],
            video_details['likeCount'],
            video_details['favoriteCount'],
            video_details.get('commentCount', 'disable'),
            1 if video_contentDetails['licensedContent'] else 0,
            int(datetime.now(ho_chi_minh_tz).timestamp())
        )
        all_video_details.append(row)
    return all_video_details


def get_detail_channels(channel_ids):
    ho_chi_minh_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    all_channel_details = []
    response = youtube.channels().list(
        part='statistics,snippet,contentDetails',
        id=','.join(channel_ids)
    ).execute()
    for channel_detail in response['items']:
        # Extract channel details
        statistics = channel_detail['statistics']
        snippet = channel_detail['snippet']

        row = (
            channel_detail['id'],
            snippet.get('title', 'unknown'),
            snippet.get('country', 'unknown'),
            int(convert_datetime(snippet.get('publishedAt', 'unknown'))),
            statistics.get('viewCount', 'unknown'),
            statistics.get('subscriberCount', 'unknown'),
            statistics.get('videoCount', 'unknown')
        )
        all_channel_details.append(row)
    return all_channel_details


def producer_channel(path: str = "C:/MyDataProject/Kafka/Youtube_project2/data/channel/channel_details.parquet",
                     connection=None, cursor=None, database=None):
    # Switch to youtube database
    cursor.execute(f"USE {database}")
    # Load the Parquet file into a DataFrame
    df = pd.read_parquet(path)
    channel_ids = df['channel_id'].tolist()
    current_index = 0
    try:
        while True:
            current_index = 0 if current_index >= 100 else current_index
            batch_size = 5
            batches = channel_ids[current_index:current_index + batch_size]
            channel_updates = get_detail_channels(batches)
            cursor.executemany(channel_table_insert, channel_updates)
            connection.commit()
            current_index += 5
            print(channel_updates)
            time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    # for i, row in df.iterrows():
    #     # panda Series
    #     channel = tuple(row)
    #     print(channel)
    #     cursor.execute(channel_table_insert, channel)
    #     connection.commit()


def producer_video(path: str = "C:/MyDataProject/Kafka/Youtube_project2/data/video/video_details.parquet",
                   connection=None, cursor=None, database=None):
    # Switch to youtube database
    cursor.execute(f"USE {database}")
    # Load the Parquet file into a DataFrame
    df = pd.read_parquet(path)
    # Extract video IDs from the DataFrame
    video_ids = df['video_id'].tolist()
    current_index = 0
    try:
        while True:
            # Split sampled_video_ids into smaller batches
            current_index = 0 if current_index >= 100 else current_index
            batch_size = 5
            batches = video_ids[current_index:current_index + batch_size]
            # Process videos in parallel
            video_updates = get_detail_videos(batches)
            cursor.executemany(video_table_insert, video_updates)
            connection.commit()
            current_index += 5
            print(video_updates)
            time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")


def run_producer_channel(database=None):
    connection = create_connection()
    cursor = connection.cursor()
    producer_channel(connection=connection, cursor=cursor, database=database)
    connection.close()


def run_producer_video(database=None):
    connection = create_connection()
    cursor = connection.cursor()
    producer_video(connection=connection, cursor=cursor, database=database)
    connection.close()


if __name__ == '__main__':
    channel_process = Process(target=run_producer_channel, args=('youtube',))
    #video_process = Process(target=run_producer_video, args=('youtube',))

    # Start the processes
    channel_process.start()
    #video_process.start()

    # Wait for both processes to complete
    channel_process.join()
    #video_process.join()