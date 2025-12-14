import requests


def get_pull_requests_into_branch(git_token: str, repo: str, target_branch: str) -> list[dict]:
    """
    Get all pull requests into a given branch of a repository.

    Args:
        git_token (str): GitHub personal access token
        repo (str): Repository in 'owner/repo' format
        target_branch (str): Branch name to filter PRs into

    Returns:
        List[Dict]: List of pull request metadata dictionaries
    """
    headers = {"Authorization": f"token {git_token}", "Accept": "application/vnd.github.v3+json"}

    url = f"https://api.github.com/repos/{repo}/activity"
    params = {
        "state": "all",  # could also use "open" or "closed"
        "base": target_branch,  # only PRs targeting this base branch
        "per_page": 100,  # max GitHub page size
    }

    all_prs = []
    page = 1

    while True:
        response = requests.get(url, headers=headers, params={**params, "page": page})
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} {response.text}")

        prs = response.json()
        if not prs:
            break
        all_prs.extend(prs)
        page += 1

    return all_prs


def download_file(
    repository: str, filepath: str, owner: str, token: str = "", branch: str = "main"
):
    """
    Reads a file from a GitHub repository using a personal access token and allows specifying a branch.

    :param owner: The owner of the repository (username or organization).
    :param repository: The name of the repository.
    :param filepath: The path to the file within the repository.
    :param token: Your GitHub personal access token.
    :param branch: The branch from which to download the file (default is 'main').
    :return: The contents of the file as a string.
    """

    # Ensure correct authorization format for GitHub API
    url = f"https://api.github.com/repos/{owner}/{repository}/contents/{filepath}?ref={branch}"
    headers = {
        # "Authorization": f"Bearer {token}",  # Correct format
        "Accept": "application/vnd.github.v3.raw"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    print("headers", headers)
    # Make the request
    response = requests.get(url, headers=headers)

    # Debugging the response
    print(f"Response Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")

    # Check response
    if response.status_code == 200:
        # Check if the response text is not empty
        if response.text.strip():
            return response.text
        print("Error: Received empty response content.")
        return None
    if response.status_code == 404:
        print(f"Error: File not found at {filepath} in the {branch} branch.")
        return None
    print(
        f"Failed to fetch the file. Status code: {response.status_code}, Response: {response.text}"
    )
    response.raise_for_status()
    return None
