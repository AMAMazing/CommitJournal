import os
from github import Github, Auth, GithubException, RateLimitExceededException
from dotenv import load_dotenv
from datetime import datetime

COMMITS_FILE = "commits.txt"
MAX_COMMITS = 10

def load_token():
    """Loads the GitHub token from the .env.local file."""
    load_dotenv(dotenv_path=".env.local")
    token = os.getenv("GITHUB_TOKEN")
    # Improved check for placeholder/invalid token
    if not token or token == "YOUR_GITHUB_TOKEN_HERE" or not token.startswith(("ghp_", "gho_", "github_pat_")):
        print("Error: GitHub token not found, invalid, or seems like a placeholder in .env.local.")
        print("Please create a .env.local file and add your GitHub Personal Access Token:")
        print("GITHUB_TOKEN=your_token_here")
        print("Ensure the token has 'repo' scope (or 'public_repo' for public only).")
        return None
    return token

def get_last_commits_via_search(token, count=MAX_COMMITS):
    """
    Fetches the last 'count' commits authored or committed by the
    authenticated user using the GitHub Search API.
    """
    try:
        print("Authenticating with GitHub...")
        auth = Auth.Token(token)
        g = Github(auth=auth, per_page=100) # Increase per_page to reduce API calls if needed
        user = g.get_user()
        user_login = user.login
        print(f"Authenticated as: {user_login}")
        print(f"Searching for last {count} commits authored by {user_login}...")

        # Search for commits authored by the user, sorted by committer date (most recent first)
        # Using committer-date is generally more reliable for recency than author-date
        query = f"author:{user_login}"
        # Alternatives: f"committer:{user_login}" or f"author:{user_login} committer:{user_login}"

        commit_items = g.search_commits(query=query, sort="committer-date", order="desc")

        fetched_commits = []
        commits_processed = 0

        # The search API returns CommitSearchResult items, not full Commit objects directly sometimes
        # We need to iterate and potentially fetch the full commit if needed, but message is usually there
        for item in commit_items:
            if commits_processed >= count:
                break

            try:
                # Access commit details. item itself often has basic commit info.
                message = item.commit.message
                repo_name = item.repository.full_name
                sha_short = item.sha[:7]
                commit_date = item.commit.committer.date # Get the committer date

                # Format the output for clarity
                formatted_message = (
                    f"Repo: {repo_name}\n"
                    f"SHA: {sha_short}\n"
                    f"Date: {commit_date.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                    f"Message:\n{message}"
                )
                fetched_commits.append(formatted_message)
                commits_processed += 1

            except AttributeError as ae:
                 print(f"Warning: Could not parse commit data fully for item (SHA: {item.sha or 'unknown'}): {ae}")
            except GithubException as ge_item:
                 print(f"Warning: GitHub API error fetching details for commit {item.sha or 'unknown'}: {ge_item.status} {ge_item.data}")
            except Exception as e_item:
                 print(f"Warning: Unexpected error processing commit {item.sha or 'unknown'}: {e_item}")


        if not fetched_commits:
             print(f"No commits found authored by {user_login} via search.")
             return []

        print(f"Found {len(fetched_commits)} commits via search.")
        # We already limited the loop, but slice just in case logic changes
        return fetched_commits[:count]

    except RateLimitExceededException:
        print("Error: GitHub API rate limit exceeded. Please wait and try again later.")
        print("Rate limit info:", g.get_rate_limit())
        return None
    except GithubException as e:
        print(f"GitHub API Error: {e.status} - {e.data.get('message', 'No details')}")
        if e.status == 401:
            print("Authentication failed. Check your GITHUB_TOKEN.")
        elif e.status == 403:
             print("Forbidden. Check token scopes ('repo' or 'public_repo' needed) or potential IP restrictions.")
        elif e.status == 422:
             print(f"Unprocessable Entity. The search query '{query}' might be invalid or too complex.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def write_commits_to_file(commits, filename=COMMITS_FILE):
    """Writes a list of formatted commit details to a file."""
    if not commits:
        print("No commits to write.")
        return False
    try:
        print(f"Writing {len(commits)} commits to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            for i, commit_details in enumerate(commits):
                f.write(f"--- Commit {i+1} ---\n")
                f.write(f"{commit_details}\n")
                f.write("-" * 20 + "\n\n") # Separator
        print(f"Successfully wrote commits to {filename}.")
        return True
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")
        return False

if __name__ == "__main__":
    print("--- GitHub Commit Fetcher (Search API) ---")
    github_token = load_token()

    if github_token:
        # Use the new search-based function
        last_commits = get_last_commits_via_search(github_token, MAX_COMMITS)

        if last_commits is not None: # Check if API call was successful
             write_commits_to_file(last_commits, COMMITS_FILE)
        else:
            print("Failed to retrieve commits due to errors.")
    else:
        print("Cannot proceed without a valid GitHub token.")

    print("------------------------------------------")