import time
import requests
import pandas as pd
from sqlalchemy import create_engine
from pandas import json_normalize
from sqlalchemy import text
import psycopg2.extras

# GitHub Personal Access Token (replace with your own)
TOKEN = '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'
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


# Function to search users by city name (query)
def search_users(query, page=1, per_page=100):
    url = f"{API_BASE_URL}/search/users"
    params = {'q': query, 'page': page, 'per_page': per_page}

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()['items']  # Returns the list of users
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None


# Function to fetch all users for a specific query (city)
def fetch_all_users(query):
    page = 1
    all_users = []

    while True:
        check_rate_limit()  # Ensure we don't exceed the rate limit
        users = search_users(query, page=page)

        if not users:
            break  # Stop if there are no more users

        all_users.extend(users)
        page += 1

    return all_users


def create_city_user_table_if_not_exists(engine):
    create_table_query = """
                         CREATE TABLE IF NOT EXISTS city_user
                         (
                             id
                             SERIAL
                             PRIMARY
                             KEY,
                             user_id
                             BIGINT
                             UNIQUE,
                             login
                             TEXT
                             UNIQUE,
                             node_id
                             TEXT,
                             avatar_url
                             TEXT,
                             gravatar_id
                             TEXT
                             NULL,
                             url
                             TEXT,
                             html_url
                             TEXT,
                             followers_url
                             TEXT,
                             following_url
                             TEXT,
                             gists_url
                             TEXT,
                             starred_url
                             TEXT,
                             subscriptions_url
                             TEXT,
                             organizations_url
                             TEXT,
                             repos_url
                             TEXT,
                             events_url
                             TEXT,
                             received_events_url
                             TEXT,
                             type
                             TEXT,
                             user_view_type
                             TEXT,
                             site_admin
                             BOOLEAN,
                             score
                             FLOAT,
                             search_city
                             TEXT,
                             search_country
                             TEXT
                         ); \
                         """
    with engine.connect() as conn:
        conn.execute(text(create_table_query))
        conn.commit()


def upsert_city_users(df, engine):
    conn = engine.raw_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        # Only extract the columns that match the table
        row_dict = row.to_dict()

        keys = row_dict.keys()
        columns = ','.join(keys)
        values = ','.join(['%s'] * len(keys))
        updates = ','.join([f"{key}=EXCLUDED.{key}" for key in keys if key != 'login'])

        insert_query = f"""
        INSERT INTO city_user ({columns})
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


# Main execution
if __name__ == '__main__':
    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    # Create the SQLAlchemy engine
    engine = create_engine(connection_string)

    # Query to fetch all data from the city_location table
    query = "SELECT country, city FROM city_location;"

    # Read the data into a Pandas DataFrame (country + city)
    try:
        city_df = pd.read_sql(query, engine)  # Gets both country and city columns
        cities_users = []

        # Loop over cities to fetch users from GitHub
        for index, row in city_df[:5].iterrows():
            city = row['city']
            country = row['country']
            print(f"Fetching users for city: {city}, country: {country}")

            city_users = fetch_all_users(city)
            # Add city and country metadata to each user record
            for user in city_users:
                user['search_city'] = city
                user['search_country'] = country
                cities_users.append(user)

        # Normalize the nested JSON structure and create a DataFrame
        cities_users_df = json_normalize(cities_users)
        cities_users_df.rename(columns={'id': 'user_id'}, inplace=True)
        # print(cities_users_df[:2].to_dict())

        create_city_user_table_if_not_exists(engine)
        upsert_city_users(cities_users_df, engine)

        print("User data successfully saved to city_user table.")



    except Exception as e:
        print(f"Error: {e}")

    print(check_rate_limit(True))
