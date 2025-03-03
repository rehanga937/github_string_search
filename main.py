import os
import subprocess
from datetime import datetime
import json

# Check if all the required files are available
# -----------------------------------------------------------------------
available_files = os.listdir("input")

def all_files_available() -> bool:
    available = True

    if 'secrets.txt' not in available_files:
        available = False
        with open(os.path.join("input","secrets.txt"), "wt") as f: pass
        print("'secrets.txt' not found in the input folder. Created empty text file with its name.")

    if 'usernames.py' not in available_files: 
        available = False
        with open(os.path.join("input","usernames.py"), "wt") as f:
            # I wrote it like this cuz if I included a template file, chances are I'd edit the template file with an actual secret key and then possible commit it.
            line1 = "usernames = [\n"
            line2 = "\t(username1, token1), # strings\n"
            line3 = "\t(username2, token2)\n"
            line4 = "]"
            f.writelines([line1, line2, line3, line4])
        print("'usernames.py' not found in the input folder. Created empty text file with its name.")

    return available

if not all_files_available(): quit()
# -----------------------------------------------------------------------


# Read the input files (secrets and usernames)
# -----------------------------------------------------------------------
with open(os.path.join("input","secrets.txt"), "rt") as f:
    secrets = f.readlines()
for i in range(0,len(secrets)): 
    secrets[i] = secrets[i].strip().replace('\n','').replace('\r','')

from input import usernames as un
usernames = un.usernames

# -----------------------------------------------------------------------

# get the git clone links from the usernames' repos
# -----------------------------------------------------------------------
remotes: list[str] = []
for username in usernames:
    print(f"Processing username: {username[0]}")
    name = username[0]
    token = username[1]

    curl_output = subprocess.run(["curl", "-u", f"{name}:{token}", "https://api.github.com/user/repos?affiliation=owner"] ,shell=True, capture_output=True)
    repo_info = json.loads(curl_output.stdout)
    print(f"{len(repo_info)} repo(s) found:")
    repo_info.sort(key=lambda x:x['name'].lower())
    for repo in repo_info:
        print(repo['name'])
        remotes.append(repo['clone_url'])
    print()
# -----------------------------------------------------------------------



# clone each repo and scan entire git history for secrets
# -----------------------------------------------------------------------
os.makedirs("downloads", exist_ok=True)
storage_folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
working_directory = os.path.join("downloads", storage_folder_name)
os.makedirs(working_directory)

for remote in remotes:
    # whitelisted_remotes = ["https://github.com/.....git", "https://github.com/....git"]
    # if remote not in whitelisted_remotes: continue

    output = subprocess.run(["git", "clone", remote], shell=True, cwd=working_directory, capture_output=True)
    git_output = output.stderr.decode() # git outputs to stderr for some reason. Also we can only get the first line, not the output showing progress, but that's fine for this use-case.
    if '\nremote: Repository not found.\nfatal: repository' in git_output: 
        print(f"\033[33mRemote: {remote} not found.\033[0m \n")
        continue
    if "Cloning into" not in git_output: continue
        
    folder_name = git_output.split("'")[1]
    cloned_folders = os.listdir(working_directory)
    if folder_name not in cloned_folders:
        print(f"\033[33mDownloading remote: {remote} into folder {folder_name} failed. Skipping...\033[0m")
        continue
    print(f"Downloaded remote: {remote} into folder: {folder_name}")

    for secret in secrets:
        """git grep "<the key you leaked like a dumass>" $(git rev-list --all)"""

        # get the revision list (git rev-list --all) i.e. ALL the commit hashes
        # this command prints each commit hash on the terminal in a new line.
        # thanks https://stackoverflow.com/questions/54014165/handling-expanded-git-commands-with-python-subprocess-module
        stage1_output = subprocess.run(["git", "rev-list", "--all"], shell=True, cwd=os.path.join(working_directory,folder_name), capture_output=True)
        revision_list = stage1_output.stdout.decode().splitlines()

        cmd = ["git", "grep", secret] + revision_list
        subprocess.run(cmd, shell=True, cwd=os.path.join(working_directory,folder_name)) # since capture_output argument isn't given, this will print the output on the terminal



    print()
# -----------------------------------------------------------------------