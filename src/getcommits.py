import os
import base64 # Added for decoding README content
from github import Github, Auth, GithubException, RateLimitExceededException
from dotenv import load_dotenv
from datetime import datetime

COMMITS_FILE = "output/commits.txt" # Updated path
MAX_COMMITS = 30

def load_token():
    """Loads the GitHub token from the .env.local file."""
    load_dotenv(dotenv_path=".env.local") # Assumes .env.local is in the project root (d:/CommitJournal)
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
    authenticated user using the GitHub Search API. Includes repo description and README.
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
        query = f"author:{user_login}"
        commit_items = g.search_commits(query=query, sort="committer-date", order="desc")

        fetched_commits = []
        commits_processed = 0

        # Iterate through search results
        for item in commit_items:
            if commits_processed >= count:
                break

            try:
                # Access commit details
                message = item.commit.message
                repo = item.repository # Get the repository object
                repo_name = repo.full_name
                # --- Get Repository Description ---
                repo_description = repo.description if repo.description else "No description available"
                # --- Get README Content ---
                readme_content = "Could not fetch README." # Default message
                try:
                    readme_file = repo.get_readme()
                    # Decode base64 content
                    readme_content = base64.b64decode(readme_file.content).decode('utf-8')
                    print(f"Successfully fetched README for {repo_name}")
                except GithubException as ge_readme:
                    if ge_readme.status == 404:
                        readme_content = "No README file found in this repository."
                        print(f"No README found for {repo_name}")
                    else:
                        # Handle other potential GitHub errors when fetching README
                        readme_content = f"Error fetching README: {ge_readme.status} {ge_readme.data}"
                        print(f"Warning: GitHub API error fetching README for {repo_name}: {ge_readme.status} {ge_readme.data}")
                except Exception as e_readme:
                    # Catch any other unexpected error during README fetching/decoding
                    readme_content = f"Unexpected error processing README: {e_readme}"
                    print(f"Warning: Unexpected error processing README for {repo_name}: {e_readme}")
                # ---
                sha_short = item.sha[:7]
                commit_date = item.commit.committer.date # Get the committer date

                # Format the output for clarity, now including the description and README
                # Use parentheses for multi-line f-string
                formatted_message = (
                    f"Repo: {repo_name}\n"
                    f"Description: {repo_description}\n"
                    f"SHA: {sha_short}\n"
                    f"Date: {commit_date.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                    f"Message:\n{message}\n\n" # Double newline before README
                    f"--- README ---\n{readme_content}" # Added README section
                )
                fetched_commits.append(formatted_message)
                commits_processed += 1

            except AttributeError as ae:
                 # This might happen if expected attributes (like commit, repository) are missing
                 print(f"Warning: Could not parse commit data fully for item (SHA: {getattr(item, 'sha', 'unknown')}): {ae}")
            except GithubException as ge_item:
                 # Error specifically related to fetching data for this item
                 print(f"Warning: GitHub API error fetching details for commit {getattr(item, 'sha', 'unknown')}: {ge_item.status} {ge_item.data}")
            except Exception as e_item:
                 # Catch any other unexpected error during item processing
                 print(f"Warning: Unexpected error processing commit {getattr(item, 'sha', 'unknown')}: {e_item}")


        if not fetched_commits:
             print(f"No commits found authored by {user_login} via search.")
             return []

        print(f"Found {len(fetched_commits)} commits via search.")
        return fetched_commits[:count] # Ensure we only return max 'count'

    except RateLimitExceededException:
        print("Error: GitHub API rate limit exceeded. Please wait and try again later.")
        try:
            rate_limit = g.get_rate_limit()
            print(f"Rate Limit Info: Core Remaining: {rate_limit.core.remaining}, Search Remaining: {rate_limit.search.remaining}")
            reset_time = datetime.fromtimestamp(rate_limit.search.reset)
            print(f"Search Rate Limit Resets At: {reset_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except Exception as rl_err:
            print(f"Could not retrieve rate limit details: {rl_err}")
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
        # Ensure the output directory exists
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            print(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        print(f"Writing {len(commits)} commits to {filename}...")
        # Use 'w' mode which overwrites the file. Ensure utf-8 encoding.
        # Python's text mode handles line endings (\n -> \r\n on Windows)
        with open(filename, 'w', encoding='utf-8') as f:
            for i, commit_details in enumerate(commits):
                f.write(f"--- Commit {i+1} ---\n")
                f.write(f"{commit_details}\n") # commit_details now includes README
                # Use the original separator format, followed by two newlines
                f.write("--------------------\n\n")
        print(f"Successfully wrote commits to {filename}.")
        return True
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")
        return False
    except OSError as e:
        print(f"Error creating directory for {filename}: {e}")
        return False


if __name__ == "__main__":
    print("--- GitHub Commit Fetcher (Search API) ---")
    github_token = load_token()

    if github_token:
        last_commits = get_last_commits_via_search(github_token, MAX_COMMITS)

        if last_commits is not None: # Check if API call was successful
             # Pass the correct filename variable here
             write_commits_to_file(last_commits, COMMITS_FILE)
        else:
            print("Failed to retrieve commits due to errors.")
    else:
        print("Cannot proceed without a valid GitHub token.")

    print("------------------------------------------")
