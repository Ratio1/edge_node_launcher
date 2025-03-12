import requests
import json


class ReleaseChecker:
  
  def __init__(self) -> None:
    self.cfg_releases_repo_url = "https://api.github.com/repos/Ratio1/edge_node_launcher"
    self.cfg_nr_previous_releases = 10
    self.requests = requests
    return
  
  def P(self, msg):
    print(msg, flush=True)
    return

  def get_latest_releases(self):
    releases_url = f"{self.cfg_releases_repo_url}/releases"
    self.P("Requesting releases from: {}".format(releases_url))
    response = self.requests.get(releases_url, params={"per_page": self.cfg_nr_previous_releases + 1})
    releases = response.json()
    return releases


  # Fetch the last 10 tags
  def get_latest_tags(self):
    tags_url = f"{self.cfg_releases_repo_url}/tags"
    self.P("Requesting tags from: {}".format(tags_url))
    response = self.requests.get(tags_url, params={"per_page": self.cfg_nr_previous_releases + 1})
    tags = response.json()
    return tags


  def get_commit_info(self, commit_sha):    
    commit_url = f"{self.cfg_releases_repo_url}/commits/{commit_sha}"
    self.P("Requesting commit info from: {}".format(commit_url))
    response = self.requests.get(commit_url)
    commit_info = response.json()
    return commit_info


  def compile_release_info(self, releases, tags):
    for release in releases:
      release_tag = release['tag_name'].strip("'")
      tag = next((tag for tag in tags if tag['name'].strip("'") == release_tag), None)

      if tag:
        commit_info = self.get_commit_info(tag['commit']['sha'])
        release['commit_info'] = commit_info
      else:
        release['commit_info'] = None
      # end if
    return releases  
  
  
if __name__ == "__main__":
  rc = ReleaseChecker()
  releases = rc.get_latest_releases()
  tags = rc.get_latest_tags()
  release_info = rc.compile_release_info(releases, tags)
  releases.sort(key=lambda x: x['published_at'], reverse=True)
  latest_release = releases[0]
  print(json.dumps(latest_release, indent=2))
  print("Done.")