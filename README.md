# Commit Journal

This script fetches your 50 most recent GitHub commit events (specifically, commits from `PushEvent`s) and compares them against a locally stored list (`commits.txt`). It outputs any new commit SHAs found since the last run and then updates `commits.txt` with the latest set of 50 commit SHAs.

## Features

- Fetches the 50 most recent commit SHAs associated with your GitHub account's push events.
- Compares fetched commits with a stored list to identify new ones.
- Updates the stored list for future comparisons.
- Supports accessing private repositories using a GitHub Personal Access Token (PAT).

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository_url>
    cd CommitJournal
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    - Windows (cmd): `venv\Scripts\activate`
    - Windows (PowerShell): `venv\Scripts\Activate.ps1`
    - macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You'll create `requirements.txt` in the next step)*

4.  **Create `requirements.txt`:**
    Create a file named `requirements.txt` in the project root with the following content:
    ```
    PyGithub
    python-dotenv
    ```
    Then run `pip install -r requirements.txt`.

5.  **Set up GitHub Token:**
    - **Generate a Personal Access Token (PAT):**
        - Go to your GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic).
        - Click "Generate new token" (or "Generate new token (classic)").
        - Give it a descriptive name (e.g., "CommitJournalScript").
        - Set an expiration date.
        - Select the necessary scopes. For reading commit history (including private repos you have access to), you might need scopes like `repo` (full control of private repositories) or potentially `read:user` and `read:org` depending on your needs. Start with minimal permissions and add more if required.
        - Click "Generate token".
        - **Important:** Copy the token immediately. You won't be able to see it again.
    - **Create `.env.local` file:**
        Create a file named `.env.local` in the project root (d:/CommitJournal).
    - **Add token to `.env.local`:**
        Open `.env.local` and add the following line, replacing `YOUR_GITHUB_TOKEN_HERE` with the PAT you just generated:
        ```
        GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
        ```
        This file is included in `.gitignore` to prevent accidentally committing your token.

## Usage

Run the script from your terminal in the project's root directory (`d:/CommitJournal`):

```bash
python commit_tracker.py


The script will:

Attempt to load the GITHUB_TOKEN from .env.local.

Authenticate with GitHub using the token.

Fetch your user information and the latest 50 commit SHAs from your push events.

Read the previously stored commit SHAs from commits.txt (if it exists).

Print any new commit SHAs found.

Overwrite commits.txt with the latest 50 fetched commit SHAs.

The first time you run it, it might list all 50 commits as "new" since commits.txt will be empty or non-existent. Subsequent runs will only show commits made since the last execution.

How it Works

load_token(): Reads the GITHUB_TOKEN from the .env.local file using python-dotenv.

get_stored_commits(): Reads commit SHAs from commits.txt. Returns an empty set if the file doesn't exist.

fetch_and_compare_commits():

Authenticates with GitHub using the token via PyGithub.

Fetches the authenticated user's event stream.

Iterates through events, looking for PushEvents.

Extracts commit SHAs from the commits list within the PushEvent payload.

Collects up to 50 recent commit SHAs.

Compares the fetched SHAs with the stored SHAs.

Prints the difference (new commits).

Returns the list of recently fetched SHAs.

update_commits_file(): Writes the list of recently fetched commit SHAs to commits.txt, overwriting its previous content.

if __name__ == "__main__":: The main execution block that calls the fetch and update functions.

Notes

The script fetches commit events for the authenticated user across all repositories they have pushed to. It stops after finding 50 commit SHAs within these push events.

Error handling is basic. It includes checks for the token and general exceptions during API calls or file operations.
