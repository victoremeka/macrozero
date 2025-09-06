import requests

# Personal Access Token (replace with your actual token)
ACCESS_TOKEN = "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
USERNAME = "your_github_username"
REPO_NAME = "your_repository_name"

# Example: Get a user's public repositories
def get_user_repos(username):
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {ACCESS_TOKEN}"  # For authenticated requests
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Example: Create a new repository (requires appropriate scopes on your token)
def create_repo(repo_name, description=""):
    url = "https://api.github.com/user/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {ACCESS_TOKEN}"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": False  # Set to True for private repository
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully.")
        return response.json()
    else:
        print(f"Error creating repository: {response.status_code} - {response.text}")
        return None

# Usage example
# repos = get_user_repos(USERNAME)
# if repos:
#     for repo in repos:
#         print(repo['name'])

# create_repo("my-new-repo", "A repository created via GitHub API in Python.")