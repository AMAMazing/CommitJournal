# Commit Journal

Commit Journal is a Python-based tool designed to fetch and log your recent GitHub commits. It uses the GitHub API to retrieve your latest commit activity, including repository details and the associated README files, and organizes this information into local text files. This is particularly useful for keeping a running log of your work or for feeding your commit history into other systems, such as AI models for summarization or analysis.

## Features

- Fetches the 30 most recent commits authored by the authenticated user.
- For each commit, it retrieves the repository name, description, commit message, date, and the full content of the repository's README file.
- Differentiates between all fetched commits and commits that are new since the last run.
- Outputs logs to separate files for all commits (`output/commits.txt`) and new commits (`output/new_commits.txt`).
- Handles GitHub API rate limiting gracefully and provides informative error messages.

## Prerequisites

- Python 3.x
- A GitHub Personal Access Token (PAT) with `repo` scope (or `public_repo` for public repositories only).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd CommitJournal
    ```

2.  **Install dependencies:**
    This project uses `PyGithub` and `python-dotenv`. Install them using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create an environment file:**
    Create a file named `.env.local` in the root directory of the project. This file will store your GitHub token securely.

4.  **Add your GitHub Token:**
    Open the `.env.local` file and add your GitHub Personal Access Token in the following format:
    ```
    GITHUB_TOKEN=your_personal_access_token_here
    ```
    Replace `your_personal_access_token_here` with your actual token.

## How to Run

Execute the main script from the root directory:

```bash
python src/getcommits.py
```

The script will:
1.  Authenticate with the GitHub API using your token.
2.  Fetch your latest commits.
3.  Identify which of those commits are new since the last run.
4.  Write the logs to the `output/` directory.

## Output Files

The script generates two files in the `output/` directory:

-   `output/commits.txt`: This file is overwritten on every run and contains the full list of the 30 most recent commits fetched from GitHub.
-   `output/new_commits.txt`: This file contains only the commits that have been made since the script was last executed. If no new commits are found, this file will be empty.

Each entry in the output files is formatted to be easily readable, including repository information, commit details, and the full README content.