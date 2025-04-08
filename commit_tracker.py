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
        with open(COMMITS_FILE, "r") as f:
            # Read lines, strip whitespace, and filter out empty lines
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def fetch_and_compare_commits():
    """Fetches the 50 most recent commits and outputs the new ones."""
    token = load_token()
    if not token:
        return None

    try:
        # Authenticate using token for private repo access if needed
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user() # Gets the authenticated user

        print(f"Fetching commits for user: {user.login}")

        # Get the 50 most recent commit events for the authenticated user
        # Note: This fetches events across all repos the user pushed to.
        events = user.get_events()
        recent_commits = []
        commit_count = 0
        # Iterate through events, find PushEvents, and extract commit SHAs
        for event in events:
            if event.type == 'PushEvent':
                # Get commits from the payload, ensuring payload['commits'] exists
                commits_in_push = event.payload.get('commits', [])
                for commit in commits_in_push:
                    # Check if 'sha' exists in the commit details
                    if 'sha' in commit:
                         recent_commits.append(commit['sha'])
                         commit_count += 1
                         if commit_count >= 50:
                             break # Stop after getting 50 commits
            if commit_count >= 50:
                break # Stop iterating through events

        if not recent_commits:
             print("No recent push events with commits found.")
             # Return empty list if no commits, allows update_commits_file to clear the file
             return []


        stored_commits = get_stored_commits()
        new_commits = [sha for sha in recent_commits if sha not in stored_commits]

        if new_commits:
            print("\nNew commits found:")
            for sha in new_commits:
                # For simplicity, just printing the SHA.
                # Getting repo/message requires more complex API calls.
                print(f"- {sha}")
        else:
            print("\nNo new commits since last check.")

        return recent_commits # Return the fetched commits for updating the file

    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider more specific error handling for rate limits, auth errors etc.
        return None


def update_commits_file(commits_to_store):
    """Updates the commits file with the latest list of commit SHAs."""
    if commits_to_store is None:
        print("Skipping update of commits file due to previous errors.")
        return

    try:
        # Write only the most recent SHAs fetched (up to 50)
        with open(COMMITS_FILE, "w") as f:
            for sha in commits_to_store:
                f.write(sha + "\n")
        print(f"\nUpdated {COMMITS_FILE} with the latest {len(commits_to_store)} commit SHAs.")
    except Exception as e:
        print(f"Error writing to {COMMITS_FILE}: {e}")


if __name__ == "__main__":
    print("Checking for new commits...")
    # Need to install dependencies first: pip install PyGithub python-dotenv
    try:
        latest_commits = fetch_and_compare_commits()
        if latest_commits is not None: # Only update if fetching was successful or returned empty list
            update_commits_file(latest_commits)
    except NameError:
         print("Error: Required libraries not found.")
         print("Please install them by running: pip install PyGithub python-dotenv")
    except Exception as e:
         print(f"An unexpected error occurred in main execution: {e}")
