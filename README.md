# CartesianLabs Test

# _GitHub User Data Scraping_

This project scrapes GitHub user data based on city information and stores it in a PostgreSQL database. It is designed
to:

- Fetch GitHub users by city and country from a PostgreSQL database.
- Save user details and followers' information into respective tables.
- Handle GitHub rate limits efficiently to ensure smooth data retrieval.

## Prerequisites

1. Docker
2. PostgreSQL 15 or compatible
3. Python 3.x
4. GitHub Personal Access Token (PAT)

## Setup

### 1. **Run PostgreSQL with Docker**

First, set up PostgreSQL using Docker:

```bash
docker-compose up -d
```

This will start a PostgreSQL container with persistent storage.

### 2. **Configure the Scripts**

- **GitHub Token**: In `city_user.py`, `user.py`, and `user_followers.py`, replace `'your_key'` with your own GitHub
  Personal Access Token (PAT).

  You can generate a PAT from your GitHub settings:  
  [GitHub Tokens](https://github.com/settings/tokens)

- **Database Configuration**: The PostgreSQL connection details are configured in each script. If you're using different
  database credentials or settings, update the `host`, `port`, `dbname`, `user`, and `password` variables accordingly.

### 3. **Running the Scripts**

1. **`city_user.py`**: This script fetches users based on city and country data stored in the `city_location` table. It
   scrapes GitHub user details and stores them in the `city_user` table.

   To run:
   ```bash
   python city_user.py
   ```

2. **`user.py`**: This script fetches additional user information (like bio, company, followers, etc.) for users stored
   in the `city_user` table. It stores the enriched data in the `users` table.

   To run:
   ```bash
   python user.py
   ```

3. **`user_followers.py`**: This script scrapes the followers of users stored in the `users` table and saves the
   followers' data in the `user_followers` table.

   To run:
   ```bash
   python user_followers.py
   ```

### 4. **Database Structure**

- `city_location`: Contains city and country information.
- `city_user`: Stores GitHub user information fetched based on cities.
- `users`: Contains enriched user data (bio, location, followers, etc.).
- `user_followers`: Stores information about user followers.

### 5. **Rate Limit Handling**

- The scripts include functions to check and handle GitHub API rate limits to ensure smooth scraping.
- If the rate limit is about to be exceeded, the script will wait until the limit resets.

### 6. **Dependencies**

Ensure the following Python dependencies are installed:

```bash
pip install -r requirements.txt
```

Where `requirements.txt` contains:

```
requests
pandas
sqlalchemy
psycopg2
```

## Troubleshooting

- **Rate Limits**: If you are scraping a large number of users, ensure you're using an authenticated GitHub token to
  increase your API rate limit (5,000 requests per hour).
- **Database Connection**: Make sure the PostgreSQL container is running and accessible at the correct `host` and
  `port`.
