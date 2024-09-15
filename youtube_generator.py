import requests
import json
import os
import psycopg2
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytz
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("API_KEY")
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


def get_top_video(type: str = 'games', max_results: int = 100):
    url = "https://www.googleapis.com/youtube/v3/search"

    # Define parameters
    params = {
        'part': 'snippet',
        'type': 'video',
        'order': 'viewCount',  # Order by view count
        'maxResults': 50,  # Maximum number of results per request
        'key': API_KEY,
        'regionCode': 'US',  # Optional: Filter by region code
        'channelType': 'any',
        'eventType': 'completed',
        'q': type,
        'publishedAfter': '2023-01-01T00:00:00Z',  # Optional: Filter by publication date
        'publishedBefore': '2024-01-01T00:00:00Z',  # Optional: End date filter
    }

    videos = []
    while len(videos) < max_results:
        response = requests.get(url, params=params)
        data = response.json()

        # Extract and append the video details
        for item in data.get('items', []):
            video_title = item['snippet']['title']
            video_id = item['id']['videoId']
            channel_title = item['snippet']['channelTitle']
            video_description = item['snippet']['description']
            videos.append({
                'video_title': video_title,
                'video_id': video_id,
                'channel_title': channel_title,
                'video_description': video_description
            })

        # Check if there are more pages
        next_page_token = data.get('nextPageToken')
        if not next_page_token or len(videos) >= max_results:
            break

        # Update the parameters for the next request
        params['pageToken'] = next_page_token

    # Print the results
    for i, video in enumerate(videos[:max_results], 1):
        print(
            f"{i}. Title: {video['video_title']}\n   Channel: {video['channel_title']}\n   Video ID: {video['video_id']}\n")

    # Write the data to JSON file
    with open('data/youtube_games_videos.json', 'w') as file:
        json.dump(videos, file, indent=4)


def get_details_video(path: str = './data/youtube_games_videos.json'):
    # Time zone for Ho Chi Minh City
    ho_chi_minh_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    all_video_details = []
    # Open the path
    with open(path, 'r') as file:
        videos = json.load(file)

    for i, item in enumerate(videos, 1):
        video_id = item['video_id']
        response = youtube.videos().list(
            part='statistics,snippet,contentDetails',
            id=video_id
        ).execute()
        video_details = response['items'][0]['statistics']
        video_snippet = response['items'][0]['snippet']
        video_contentDetails = response['items'][0]['contentDetails']
        # print(video_details)
        row = {
            'video_id': video_id,
            'channel_id': video_snippet['channelId'],
            'video_title': video_snippet['title'],
            'video_duration': video_contentDetails['duration'],
            'video_viewCount': video_details['viewCount'],
            'video_likeCount': video_details['likeCount'],
            'video_favoriteCount': video_details['favoriteCount'],
            'video_commentCount': video_details.get('commentCount', 'disable'),
            'video_licensedContent': 1 if video_contentDetails['licensedContent'] else 0,
            'update_at': int(datetime.now(ho_chi_minh_tz).timestamp())
        }
        all_video_details.append(row)

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(all_video_details)

    # Write the dataframe to a Parquet file
    df.to_parquet('./data/video/video_details.parquet', engine='pyarrow', index=False)


def get_channelIds(path: str = './data/youtube_games_videos.json'):
    channelIds = []
    # Open the path
    with open(path, 'r') as file:
        videos = json.load(file)

    for i, item in enumerate(videos, 1):
        video_id = item['video_id']
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        channelId = response['items'][0]['snippet']['channelId']
        channelIds.append(channelId)

    return channelIds


def get_channel_details(channelIds):
    all_channel_details = []
    for channelId in channelIds:
        response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            id=channelId
        ).execute()
        # Extract channel details
        channel_details = response['items'][0]
        statistics = channel_details['statistics']
        snippet = channel_details['snippet']

        row = {
            'channel_id': channelId,
            'title': snippet.get('title', 'unknown'),
            'country': snippet.get('country', 'unknown'),
            'published_at': convert_datetime(snippet.get('publishedAt', 'unknown')),
            'view_count': statistics.get('viewCount', 'unknown'),
            'subscriber_count': statistics.get('subscriberCount', 'unknown'),
            'video_count': statistics.get('videoCount', 'unknown')
        }
        all_channel_details.append(row)

    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(all_channel_details)

    # Write the dataframe to a Parquet file
    df.to_parquet('./data/channel/channel_details.parquet', engine='pyarrow', index=False)


# def main():
#     conn = psycopg2.connect("host=192.168.1.8 dbname=youtube user=postgres password=26102002 port=5433")
#     cur = conn.cursor()
#     conn.close()


if __name__ == '__main__':
    get_top_video(type='games', max_results=100)
    get_details_video(path='./data/youtube_games_videos.json')
    channelIds = get_channelIds(path="./data/youtube_games_videos.json")
    get_channel_details(channelIds)
