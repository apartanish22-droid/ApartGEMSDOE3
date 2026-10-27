from pathlib import Path

import yaml

from conftest import ROOT


def test_scheduled_pages_workflow_is_read_only_on_git_and_pr_cannot_publish():
    path = ROOT / ".github/workflows/pages.yml"
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert workflow["on"]["schedule"] and "pull_request" in workflow["on"]
    assert workflow["permissions"]["contents"] == "read"
    jobs = workflow["jobs"]
    assert jobs["publish"]["needs"] == "test"
    assert "pull_request" in jobs["publish"]["if"]
    assert jobs["publish"]["permissions"]["contents"] == "read"
    content = path.read_text().lower()
    assert "git push" not in content and "git commit" not in content
    assert "actions/cache/restore@" in content and "actions/cache/save@" in content
    assert "scripts/refresh_feed.py" in content and "actions/deploy-pages@" in content
    # Do not accidentally redistribute the ignored upstream template.
    assert "cp -r assets docs evidence registry scripts vendor" not in content
