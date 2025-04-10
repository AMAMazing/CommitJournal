import os
from github import Github, Auth
from dotenv import load_dotenv

COMMITS_FILE = "commits.txt"

def load_token():
    """Loads the GitHub token from the .env.local file."""
    load_dotenv(dotenv_path=".env.local")
    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "YOUR_GITHUB_TOKEN_HERE":
        print("Error: GitHub token not found or not set in .env.local.")
        print("Please create a .env.local file and add your GitHub Personal Access Token:")
        print("GITHUB_TOKEN=your_token_here")
        return None
    return token

def get_stored_commits():
    """Reads the list of stored commit SHAs from the file."""
    try:
        # Explicitly use utf-8 encoding, robust against different environments
        with open(COMMITS_FILE, "r", encoding="utf-8") as f:
            # Read lines, strip whitespace/newlines, and filter out empty lines
            # This ensures clean SHAs for comparison
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        # Create the file if it doesn't exist, also using utf-8
        try:
            with open(COMMITS_FILE, 'a', encoding="utf-8") as f:
                 pass # Just create the file if it doesn't exist
        except Exception as e:
             print(f"Error creating {COMMITS_FILE}: {e}")
        return set()
    except Exception as e:
        print(f"Error reading {COMMITS_FILE}: {e}")
        return set() # Return empty set on other read errors

def fetch_and_compare_commits():
    """Fetches the 10 most recent commits, prints the new ones, and returns them."""
    token = load_token()
    if not token:
        return None

    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()

        print(f"Fetching commits for user: {user.login}")

        events = user.get_events()
        recent_commits_shas = []
        commit_count = 0
        # Using a set to automatically handle potential duplicate SHAs from the API fetch
        unique_fetched_shas = set()

        for event in events:
            if event.type == 'PushEvent':
                commits_in_push = event.payload.get('commits', [])
                for commit in commits_in_push:
                    if 'sha' in commit:
                        sha = commit['sha']
                        # Add to set to track uniqueness and count
                        if sha not in unique_fetched_shas:
                            unique_fetched_shas.add(sha)
                            recent_commits_shas.append(sha) # Keep order if needed, though set handles uniqueness
                            commit_count += 1
                            if commit_count >= 10: # Changed limit from 50 to 10
                                break
            if commit_count >= 10: # Changed limit from 50 to 10
                break

        if not recent_commits_shas:
             print("No recent push events with commits found.")
             return []

        stored_commits = get_stored_commits()
        # Debug print (optional, can be removed later)
        # print(f"DEBUG: Stored commits count: {len(stored_commits)}")
        # print(f"DEBUG: Fetched commits count: {len(recent_commits_shas)}")

        # Identify commits that are in the fetched list but not stored yet
        new_commits = [sha for sha in recent_commits_shas if sha not in stored_commits]

        if new_commits:
            print("\nNew commits found:")
            for sha in new_commits:
                print(f"- {sha}")
        else:
            print("\nNo new commits since last check.")

        # Return only the list of new commit SHAs
        return new_commits

    except Exception as e:
        print(f"An error occurred during fetch/compare: {e}")
        return None


def append_new_commits_to_file(new_commits_to_append):
    """Appends the list of new commit SHAs to the commits file."""
    if new_commits_to_append is None:
        print("Skipping update of commits file due to errors during fetch.")
        return
    if not new_commits_to_append:
        # No new commits were found, no need to write to the file
        # Keep the confirmation message consistent, maybe indicate nothing was appended
        # print(f"\nNo new commits to append to {COMMITS_FILE}.")
        return # Silently return if no new commits

    try:
        # Open in append mode ('a') with explicit utf-8 encoding
        with open(COMMITS_FILE, "a", encoding="utf-8") as f:
            count_appended = 0
            for sha in new_commits_to_append:
                # Use os.linesep for platform-independent newline writing
                f.write(sha + os.linesep)
                count_appended += 1
        # Report the actual number appended
        print(f"\nAppended {count_appended} new commit SHAs to {COMMITS_FILE}.")
    except Exception as e:
        print(f"Error writing to {COMMITS_FILE}: {e}")


if __name__ == "__main__":
    print("Checking for new commits...")
    # Need to install dependencies first: pip install PyGithub python-dotenv
    try:
        new_commit_shas = fetch_and_compare_commits()
        if new_commit_shas is not None: # Check if fetch was successful (returned a list)
            append_new_commits_to_file(new_commit_shas)
    except NameError:
         print("Error: Required libraries not found.")
         print("Please install them by running: pip install PyGithub python-dotenv")
    except Exception as e:
         print(f"An unexpected error occurred in main execution: {e}")
