channel_table_drop = "DROP TABLE IF EXISTS Channel"
video_table_drop = "DROP TABLE IF EXISTS Video"

channel_table_create = """
    CREATE TABLE IF NOT EXISTS Channel
    (
        channel_id VARCHAR(50),
        title VARCHAR(2000),
        country VARCHAR(100),
        published_at BIGINT,
        view_count VARCHAR(50),
        subscriber_count VARCHAR(50),
        video_count VARCHAR(50),
        PRIMARY KEY (channel_id)
    )
"""

video_table_create = """
    CREATE TABLE IF NOT EXISTS Video
    (
        video_id VARCHAR(50),
        channel_id VARCHAR(50),
        video_title VARCHAR(2000),
        video_duration VARCHAR(50),
        video_viewCount VARCHAR(50),
        video_likeCount VARCHAR(50),
        video_favoriteCount VARCHAR(50),
        video_commentCount VARCHAR(50),
        video_licensedContent INTEGER,
        update_at BIGINT,
        PRIMARY KEY (video_id, update_at),
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id)
    )
"""

# Insert records for Channel with ON DUPLICATE KEY UPDATE for conflict handling
channel_table_insert = """
    INSERT INTO Channel (channel_id, title, country, published_at, view_count, subscriber_count, video_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        title = VALUES(title),
        country = VALUES(country),
        published_at = VALUES(published_at),
        view_count = VALUES(view_count),
        subscriber_count = VALUES(subscriber_count),
        video_count = VALUES(video_count)
"""

# Insert records for Video with ON DUPLICATE KEY UPDATE for conflict handling
video_table_insert = """
    INSERT INTO Video (video_id, channel_id, video_title, video_duration, video_viewCount, video_likeCount, video_favoriteCount, video_commentCount, video_licensedContent, update_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        channel_id = VALUES(channel_id),
        video_title = VALUES(video_title),
        video_duration = VALUES(video_duration),
        video_viewCount = VALUES(video_viewCount),
        video_likeCount = VALUES(video_likeCount),
        video_favoriteCount = VALUES(video_favoriteCount),
        video_commentCount = VALUES(video_commentCount),
        video_licensedContent = VALUES(video_licensedContent),
        update_at = VALUES(update_at)
"""

# Query lists
create_table_queries = [channel_table_create, video_table_create]
drop_table_queries = [video_table_drop, channel_table_drop]
