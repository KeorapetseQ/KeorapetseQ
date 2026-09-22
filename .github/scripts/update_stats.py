import os
import re
import requests

USERNAME = "KeorapetseQ"
TOKEN = os.getenv("METRICS_TOKEN")
SVG_PATH = "assets/cosmic_dashboard.svg"

# GraphQL Query to fetch real stats, top tech stack, and top pinned/recent repositories
query = """
query($username: String!) {
  user(login: $username) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        stargazerCount
        primaryLanguage {
          name
        }
        languages(first: 3, orderBy: {field: SIZE, direction: DESC}) {
          nodes {
            name
          }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

def fetch_github_stats():
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Query failed with status {response.status_code}: {response.text}")
        
    res_json = response.json()
    if "errors" in res_json:
        raise Exception(f"GraphQL Errors: {res_json['errors']}")

    data = res_json["data"]["user"]
    
    repos_nodes = data["repositories"]["nodes"]
    repos_count = data["repositories"]["totalCount"]
    stars_count = sum(repo["stargazerCount"] for repo in repos_nodes)
    commits_count = (
        data["contributionsCollection"]["totalCommitContributions"] +
        data["contributionsCollection"]["restrictedContributionsCount"]
    )
    contributions_count = data["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    # Extract Top Tech Stack (Languages)
    lang_counts = {}
    for repo in repos_nodes:
        for lang in repo["languages"]["nodes"]:
            l_name = lang["name"]
            lang_counts[l_name] = lang_counts.get(l_name, 0) + 1
            
    top_langs = sorted(lang_counts.keys(), key=lambda x: lang_counts[x], reverse=True)[:3]
    while len(top_langs) < 3:
        top_langs.append("Code")

    # Extract Top 3 Real Projects
    top_projects = []
    for repo in repos_nodes[:3]:
        langs = [l["name"] for l in repo["languages"]["nodes"]]
        top_projects.append({
            "name": repo["name"].upper()[:20],
            "stack": " • ".join(langs) if langs else "Software",
            "desc": (repo["description"] or "Personal software project.")[:42]
        })

    return {
        "stars": stars_count,
        "repos": repos_count,
        "commits": commits_count,
        "contributions": contributions_count,
        "langs": top_langs,
        "projects": top_projects
    }

def update_svg(stats):
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Metrics Numbers
    content = re.sub(
        r'(<text [^>]*class="stat-val"[^>]*>)[^<]*(</text>)',
        lambda m, c=iter([stats['stars'], stats['repos'], stats['commits'], f"{stats['contributions']:,}"]): f"{m.group(1)}{next(c)}{m.group(2)}",
        content
    )

    # 2. Update Orbiting Stack Languages
    lang_nodes = ["Python", "TS", "C++"]
    for old_lang, new_lang in zip(lang_nodes, stats["langs"]):
        display_lang = new_lang[:6]
        content = re.sub(rf'>({old_lang})</text>', f'>{display_lang}</text>', content)

    # 3. Update Real Projects
    projects = stats["projects"]
    if len(projects) >= 3:
        # Project 1
        content = re.sub(r'MED-AI CO-PILOT', projects[0]['name'], content)
        content = re.sub(r'Python • TensorFlow • React', projects[0]['stack'], content)
        content = re.sub(r'Next-gen medical diagnostic assistant\.', projects[0]['desc'], content)

        # Project 2
        content = re.sub(r'QUANTUM BLOCKCHAIN', projects[1]['name'], content)
        content = re.sub(r'Go • Rust • IPFS', projects[1]['stack'], content)
        content = re.sub(r'Secure decentralized ledger tech\.', projects[1]['desc'], content)

        # Project 3
        content = re.sub(r'GREEN IOT GRID', projects[2]['name'], content)
        content = re.sub(r'Kubernetes • MQTT • Go', projects[2]['stack'], content)
        content = re.sub(r'Smart energy management grid\.', projects[2]['desc'], content)

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    try:
        stats = fetch_github_stats()
        print(f"Fetched Real Data: {stats}")
        update_svg(stats)
        print("Successfully updated SVG with real GitHub data!")
    except Exception as e:
        print(f"Error: {e}")
