import os
import requests

class Github:
    def __init__(self):
        self.owner = "rhombus-software"
        self.repo = "social-media-manager"
        self.workflow_file = "run_agent.yml"  # Use the actual filename in .github/workflows/
        self.branch = "main"
        self.token = os.getenv('GITHUB_TOKEN')

    def run_workflow(self, file_name):
        url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}"
            f"/actions/workflows/{self.workflow_file}/dispatches"
        )
        response = requests.post(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            json={
                "ref": branch, 
                "inputs": {
                    "file_name": file_name
                }
            },
            timeout=30,
        )

        response.raise_for_status()
        print("Workflow dispatched.")
        if response.content:
            print(response.json())



