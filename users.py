import time
import requests
import pandas as pd
from sqlalchemy import create_engine
from pandas import json_normalize
from sqlalchemy import text
import psycopg2.extras

# GitHub Personal Access Token (replace with your own)
TOKEN = 'your_key'
HEADERS = {'Authorization': f'token {TOKEN}'}

# GitHub API Base URL
API_BASE_URL = 'https://api.github.com'

# Database connection parameters
host = "localhost"
port = "5432"
dbname = "postgres"
user = "postgres"
password = "password"


# Function to check rate limit and handle sleeping if needed
def check_rate_limit(k=False):
    response = requests.get(f"{API_BASE_URL}/rate_limit", headers=HEADERS)
    data = response.json()
    remaining = data['resources']['core']['remaining']
    reset_time = data['resources']['core']['reset']
    if k:
        print(f"data: {data}")

    # If the rate limit is almost reached, sleep until it resets
    if remaining < 5:
        reset_timestamp = reset_time
        sleep_time = reset_timestamp - time.time() + 1  # Sleep until rate limit is reset
        print(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)


def create_user_table_if_not_exists(engine):
    create_table_query = """
                         CREATE TABLE IF NOT EXISTS users
                         (
                             id                  SERIAL PRIMARY KEY,
                             user_id             BIGINT UNIQUE,
                             login               TEXT UNIQUE,
                             node_id             TEXT,
                             avatar_url          TEXT,
                             gravatar_id         TEXT    NULL,
                             url                 TEXT,
                             html_url            TEXT,
                             followers_url       TEXT,
                             following_url       TEXT,
                             gists_url           TEXT,
                             starred_url         TEXT,
                             subscriptions_url   TEXT,
                             organizations_url   TEXT,
                             repos_url           TEXT,
                             events_url          TEXT,
                             received_events_url TEXT,
                             type                TEXT,
                             user_view_type      TEXT,
                             site_admin          BOOLEAN,
                             name                TEXT    NULL,
                             company             TEXT    NULL,
                             blog                TEXT    NULL,
                             location            TEXT    NULL,
                             email               TEXT    NULL,
                             hireable            BOOLEAN NULL,
                             bio                 TEXT    NULL,
                             twitter_username    TEXT    NULL,
                             public_repos        INT,
                             public_gists        INT,
                             followers           INT,
                             following           INT,
                             created_at          TIMESTAMP,
                             updated_at          TIMESTAMP
                         ); \
                         """
    with engine.connect() as conn:
        conn.execute(text(create_table_query))
        conn.commit()


def upsert_user(df, engine):
    conn = engine.raw_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        # Only extract the columns that match the table
        row_dict = row.to_dict()

        # List of the keys (column names) from the row dictionary
        keys = row_dict.keys()
        columns = ','.join(keys)
        values = ','.join(['%s'] * len(keys))
        updates = ','.join([f"{key}=EXCLUDED.{key}" for key in keys if key != 'login'])

        insert_query = f"""
        INSERT INTO users ({columns})
        VALUES ({values})
        ON CONFLICT (login) DO UPDATE SET {updates};
        """

        try:
            cursor.execute(insert_query, list(row_dict.values()))
        except Exception as e:
            print(f"Error inserting {row_dict.get('login')}: {e}")

    conn.commit()
    cursor.close()
    conn.close()


# Function to fetch user info
def get_user_info(username):
    url = f"{API_BASE_URL}/users/{username}"
    check_rate_limit()
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()
    return None


# Main execution
if __name__ == '__main__':
    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    # Create the SQLAlchemy engine
    engine = create_engine(connection_string)

    create_user_table_if_not_exists(engine)

    # Query to fetch all data from the city_location table
    query = "SELECT login FROM city_user order by id;"

    # Read the data into a Pandas DataFrame (country + city)
    try:
        city_user_df = pd.read_sql(query, engine)  # Gets both country and city columns
        users = []

        # Loop over cities to fetch users from GitHub
        for index, row in city_user_df[:50].iterrows():
            login = row['login']

            print(f"Fetched user : {login}")
            user = get_user_info(login)
            # Add city and country metadata to each user record
            users.append(user)

        # Normalize the nested JSON structure and create a DataFrame
        users_df = json_normalize(users)
        users_df.rename(columns={'id': 'user_id'}, inplace=True)
        print(users_df.head())
        # print(cities_users_df[:2].to_dict())

        upsert_user(users_df, engine)

        print("User data successfully saved to user table.")



    except Exception as e:
        print(f"Error: {e}")

    print(check_rate_limit(True))
