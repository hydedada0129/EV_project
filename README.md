front-end plugins path:
/home/oem/wordpress-docker/wp-data/wp-content/plugins/frontend-submission/frontend-submission.php

git and git push:
# Initialize local repo
git init

# Add remote origin
git remote add origin https://github.com/username/repo.git

# Create and switch to new branch
git checkout -b new-branch

# Stage all changes
git add .

# Commit changes
git commit -m "Initial commit"

# Push branch to GitHub
git push -u origin new-branch

# (Optional) Create annotated tag
git tag -a v1.0 -m "Release 1.0"

# Push tag to GitHub
git push origin v1.0
