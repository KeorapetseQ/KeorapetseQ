import os
import re
import requests

USERNAME = "KeorapetseQ"
TOKEN = os.getenv("METRICS_TOKEN")
SVG_PATH = "assets/cosmic_dashboard.svg"

# GraphQL Query to fetch total stars, repos, and commits
query = """
query($username: String!) {
  user(login: $username) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""

def fetch_github_stats():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Query failed with status {response.status_code}: {response.text}")
        
    data = response.json()["data"]["user"]
    
    # Calculate totals
    repos = data["repositories"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in data["repositories"]["nodes"])
    commits = (
        data["contributionsCollection"]["totalCommitContributions"] +
        data["contributionsCollection"]["restrictedContributionsCount"]
    )
    
    return stars, repos, commits

def update_svg(stars, repos, commits):
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex replacements matching the values in cosmic_dashboard.svg
    # Updates: <text ... class="stat-val">12</text>
    content = re.sub(
        r'(<text [^>]*class="stat-val"[^>]*>)\d+(</text>)',
        rf'\g<1>{stars}\2',
        content,
        count=1
    )
    
    # Updates second occurrence (Repos)
    matches = list(re.finditer(r'(<text [^>]*class="stat-val"[^>]*>)\d+(</text>)', content))
    if len(matches) >= 3:
        # Update Repos
        content = content[:matches[1].start(1)] + f'>{repos}<' + content[matches[1].end(2)-7:]
        # Update Commits
        content = content[:matches[2].start(1)] + f'>{commits}<' + content[matches[2].end(2)-7:]

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    try:
        stars, repos, commits = fetch_github_stats()
        print(f"Fetched Stats — Stars: {stars}, Repos: {repos}, Commits: {commits}")
        update_svg(stars, repos, commits)
        print("Successfully updated SVG stats!")
    except Exception as e:
        print(f"Error: {e}")
