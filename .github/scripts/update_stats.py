import html
import os
import re
import requests

USERNAME = "KeorapetseQ"
TOKEN = os.getenv("METRICS_TOKEN")
SVG_PATH = "assets/cosmic_dashboard.svg"

def fetch_github_stats():
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    query = """
    query($user: String!) {
      user(login: $user) {
        repositories(first: 10, orderBy: {field: STARGAZERS, direction: DESC}, ownerAffiliations: OWNER) {
          totalCount
          nodes {
            name
            description
            stargazerCount
            languages(first: 3, orderBy: {field: SIZE, direction: DESC}) {
              nodes { name }
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

    response = requests.post(url, json={'query': query, 'variables': {'user': USERNAME}}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Query failed with code {response.status_code}: {response.text}")

    data = response.json()['data']['user']

    total_stars = sum(repo['stargazerCount'] for repo in data['repositories']['nodes'])
    total_repos = data['repositories']['totalCount']
    total_commits = data['contributionsCollection']['totalCommitContributions']
    total_contributions = data['contributionsCollection']['contributionCalendar']['totalContributions']

    top_repos = data['repositories']['nodes'][:3]
    projects = []
    for repo in top_repos:
        langs = [l['name'] for l in repo['languages']['nodes']]
        
        # HTML/XML escape special characters to avoid breaking SVG syntax
        proj_name = html.escape(repo['name'].upper())
        proj_stack = html.escape(" • ".join(langs) if langs else "Code")
        proj_desc = html.escape(repo['description'] or "No description provided.")

        projects.append({
            'name': proj_name,
            'stack': proj_stack,
            'desc': proj_desc
        })

    return {
        'stars': total_stars,
        'repos': total_repos,
        'commits': total_commits,
        'contributions': total_contributions,
        'langs': ["Python", "TS", "C++"],
        'projects': projects
    }

def update_svg(stats):
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Metrics Numbers
    metrics_vals = [
        str(stats['stars']),
        str(stats['repos']),
        str(stats['commits']),
        f"{stats['contributions']:,}"
    ]

    def replace_metric(match):
        if metrics_vals:
            val = metrics_vals.pop(0)
            return f'{match.group(1)}{val}{match.group(2)}'
        return match.group(0)

    content = re.sub(
        r'(<text [^>]*class="stat-val"[^>]*>)[^<]*(</text>)',
        replace_metric,
        content
    )

    # 2. Update Default Template Placeholders
    card_defaults = [
        ("MED-AI CO-PILOT", "Python • TensorFlow • React", "Next-gen medical diagnostic assistant."),
        ("QUANTUM BLOCKCHAIN", "Go • Rust • IPFS", "Secure decentralized ledger tech."),
        ("GREEN IOT GRID", "Kubernetes • MQTT • Go", "Smart energy management grid.")
    ]

    for i, p in enumerate(stats["projects"]):
        if i < len(card_defaults):
            def_title, def_stack, def_desc = card_defaults[i]
            content = content.replace(def_title, p['name'])
            content = content.replace(def_stack, p['stack'])
            content = content.replace(def_desc, p['desc'])

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    stats = fetch_github_stats()
    update_svg(stats)