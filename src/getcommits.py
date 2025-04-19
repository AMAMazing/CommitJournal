import os
import re
import base64
from github import Github, Auth, GithubException, RateLimitExceededException
from dotenv import load_dotenv
from datetime import datetime

COMMITS_FILE = "output/commits.txt" # Path for all fetched commits
NEW_COMMITS_FILE = "output/new_commits.txt" # Path for only new commits
MAX_COMMITS = 30

def load_token():
    """Loads the GitHub token from the .env.local file."""
    load_dotenv(dotenv_path=".env.local")
    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "YOUR_GITHUB_TOKEN_HERE" or not token.startswith(("ghp_", "gho_", "github_pat_")):
        print("Error: GitHub token not found, invalid, or seems like a placeholder in .env.local.")
        print("Please create a .env.local file and add your GitHub Personal Access Token:")
        print("GITHUB_TOKEN=your_token_here")
        print("Ensure the token has 'repo' scope (or 'public_repo' for public only).")
        return None
    return token

def format_commit_details(commit_data):
    """Formats the structured commit data into a string for display/writing."""
    return (
        f"Repo: {commit_data['repo_name']}\n"
        f"Description: {commit_data['repo_description']}\n"
        f"SHA: {commit_data['sha'][:7]}\n" # Use short SHA here for consistency
        f"Date: {commit_data['commit_date'].strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Message:\n{commit_data['message']}\n\n"
        f"--- README ---\n{commit_data['readme_content']}"
    )

def get_last_commits_via_search(token, count=MAX_COMMITS):
    """
    Fetches the last 'count' commits authored by the authenticated user
    using the GitHub Search API. Includes repo description and README.
    Returns a list of dictionaries, each containing commit details.
    """
    try:
        print("Authenticating with GitHub...")
        auth = Auth.Token(token)
        g = Github(auth=auth, per_page=100)
        user = g.get_user()
        user_login = user.login
        print(f"Authenticated as: {user_login}")
        print(f"Searching for last {count} commits authored by {user_login}...")

        query = f"author:{user_login}"
        commit_items = g.search_commits(query=query, sort="committer-date", order="desc")

        fetched_commits_data = []
        commits_processed = 0

        for item in commit_items:
            if commits_processed >= count:
                break

            try:
                repo = item.repository
                repo_name = repo.full_name
                repo_description = repo.description if repo.description else "No description available"
                readme_content = "Could not fetch README."
                try:
                    readme_file = repo.get_readme()
                    readme_content = base64.b64decode(readme_file.content).decode('utf-8', errors='replace') # Handle potential decoding errors
                    print(f"Successfully fetched README for {repo_name}")
                except GithubException as ge_readme:
                    if ge_readme.status == 404:
                        readme_content = "No README file found in this repository."
                        print(f"No README found for {repo_name}")
                    else:
                        readme_content = f"Error fetching README: {ge_readme.status} {ge_readme.data.get('message', '')}"
                        print(f"Warning: GitHub API error fetching README for {repo_name}: {ge_readme.status} {ge_readme.data.get('message', '')}")
                except Exception as e_readme:
                    readme_content = f"Unexpected error processing README: {e_readme}"
                    print(f"Warning: Unexpected error processing README for {repo_name}: {e_readme}")

                commit_detail = {
                    "sha": item.sha,
                    "message": item.commit.message,
                    "repo_name": repo_name,
                    "repo_description": repo_description,
                    "readme_content": readme_content,
                    "commit_date": item.commit.committer.date
                }
                fetched_commits_data.append(commit_detail)
                commits_processed += 1

            except AttributeError as ae:
                 print(f"Warning: Could not parse commit data fully for item (SHA: {getattr(item, 'sha', 'unknown')}): {ae}")
            except GithubException as ge_item:
                 print(f"Warning: GitHub API error fetching details for commit {getattr(item, 'sha', 'unknown')}: {ge_item.status} {ge_item.data.get('message', '')}")
            except Exception as e_item:
                 print(f"Warning: Unexpected error processing commit {getattr(item, 'sha', 'unknown')}: {e_item}")


        if not fetched_commits_data:
             print(f"No commits found authored by {user_login} via search.")
             return []

        print(f"Found {len(fetched_commits_data)} commits via search.")
        # Ensure we return the correct number, although the loop condition should handle this
        return fetched_commits_data[:count]

    except RateLimitExceededException:
        print("Error: GitHub API rate limit exceeded. Please wait and try again later.")
        try:
            g = Github(auth=auth) # Re-authenticate if needed for rate limit check
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
             print(f"Unprocessable Entity. The search query might be invalid or too complex.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def read_existing_commit_shas(filename=COMMITS_FILE):
    """Reads the existing commits file and extracts short SHAs."""
    existing_shas = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all occurrences of "SHA: <7-char-sha>"
            # Regex: Looks for "SHA: " followed by exactly 7 non-whitespace characters
            sha_matches = re.findall(r"^SHA:\s*([a-fA-F0-9]{7})$", content, re.MULTILINE)
            existing_shas.update(sha_matches)
        print(f"Read {len(existing_shas)} existing SHAs from {filename}.")
    except FileNotFoundError:
        print(f"File {filename} not found. Assuming no existing commits.")
    except IOError as e:
        print(f"Error reading file {filename}: {e}")
        # Decide if we should proceed or stop. For now, proceed assuming no existing commits.
    return existing_shas

def write_commits_to_file(commits_data, filename):
    """Writes a list of structured commit data to a file, overwriting it."""
    if not commits_data:
        print(f"No commits data provided to write to {filename}.")
        return False
    try:
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            print(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        print(f"Writing {len(commits_data)} commits to {filename} (overwrite)...")
        with open(filename, 'w', encoding='utf-8') as f:
            for i, commit_detail in enumerate(commits_data):
                formatted_message = format_commit_details(commit_detail)
                f.write(f"--- Commit {i+1} ---\n")
                f.write(f"{formatted_message}\n")
                f.write("---------------------\n\n") # Separator
        print(f"Successfully wrote commits to {filename}.")
        return True
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")
        return False
    except OSError as e:
        print(f"Error creating directory for {filename}: {e}")
        return False

def write_new_commits_to_file(new_commits_data, filename=NEW_COMMITS_FILE):
    """Writes only the new commits to a separate file, overwriting it."""
    if not new_commits_data:
        print(f"No new commits to write to {filename}.")
        # It might be desirable to create an empty file or clear existing content
        # Let's clear the file if it exists but there are no new commits
        try:
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(filename, 'w', encoding='utf-8') as f:
                pass # Creates or truncates the file
            print(f"Ensured {filename} is present (or cleared).")
            return True
        except (IOError, OSError) as e:
            print(f"Error ensuring/clearing file {filename}: {e}")
            return False

    # If there are new commits, proceed with writing
    try:
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            print(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir)

        print(f"Writing {len(new_commits_data)} NEW commits to {filename} (overwrite)...")
        with open(filename, 'w', encoding='utf-8') as f:
            for i, commit_detail in enumerate(new_commits_data):
                formatted_message = format_commit_details(commit_detail)
                f.write(f"--- New Commit {i+1} ---\n") # Indicate these are new
                f.write(f"{formatted_message}\n")
                f.write("----------------------\n\n") # Separator for new commits file
        print(f"Successfully wrote new commits to {filename}.")
        return True
    except IOError as e:
        print(f"Error writing new commits to file {filename}: {e}")
        return False
    except OSError as e:
        print(f"Error creating directory for {filename}: {e}")
        return False

if __name__ == "__main__":
    print("--- GitHub Commit Fetcher (Search API) ---")
    github_token = load_token()

    if github_token:
        fetched_commits = get_last_commits_via_search(github_token, MAX_COMMITS)

        if fetched_commits is not None: # Check if API call was successful (not None)
            existing_shas = read_existing_commit_shas(COMMITS_FILE)

            # Filter for new commits
            new_commits = []
            for commit in fetched_commits:
                if commit['sha'][:7] not in existing_shas:
                    new_commits.append(commit)

            if new_commits:
                print("\n--- Found New Commits ---")
                for i, commit_data in enumerate(new_commits):
                    print(f"\n[New Commit {i+1}]")
                    print(format_commit_details(commit_data))
                    print("----------------------")
                print("--- End of New Commits ---\n")
                # Write new commits to their dedicated file
                write_new_commits_to_file(new_commits, NEW_COMMITS_FILE)
            else:
                print("\nNo new commits found since last check.")
                # Ensure the new_commits file exists but is empty
                write_new_commits_to_file([], NEW_COMMITS_FILE)


            # Always write the full fetched list to the main commits file
            write_commits_to_file(fetched_commits, COMMITS_FILE)
        else:
            print("Failed to retrieve commits due to errors.")
    else:
        print("Cannot proceed without a valid GitHub token.")

    print("------------------------------------------")
    print("Script finished.")
