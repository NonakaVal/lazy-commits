import subprocess
import os
import json
from typing import Dict, Tuple, Optional

# ========== CONFIGURATION ==========
REPO_PATH = r'C:\Users\desktop\Documents\MyApps\lazy-commits'  # Your repo path
DEFAULT_BRANCH = 'main'  # Your default branch
COUNTER_FILE = os.path.join(REPO_PATH, 'commit_counters.json')

# Improved commit messages with Conventional Commits standard
COMMIT_PURPOSES = {
    # Fixes (bug fixes - generates PATCH in semver)
    '1': 'fix: correct [issue] in [component]',  # "fix: correct typo in login error"
    '2': 'fix: resolve [bug]',                  # "fix: resolve infinite loop in parser"
    '3': 'fix: repair broken [functionality]',  # "fix: repair broken image upload"
    
    # Features (new functionality - generates MINOR in semver)
    '4': 'feat: implement [feature]',           # "feat: implement dark mode"
    '5': 'feat: add [component] to [section]',  # "feat: add pagination to dashboard"
    '6': 'feat: integrate [service/api]',       # "feat: integrate Stripe payments"
    
    # Documentation
    '7': 'docs: update [documentation]',        # "docs: update API endpoints"
    '8': 'docs: add examples for [feature]',    # "docs: add auth examples"
    
    # Code quality
    '9': 'refactor: simplify [component]',      # "refactor: simplify cart logic"
    '10': 'perf: optimize [process]',           # "perf: optimize image compression"
    '11': 'style: format [code]',               # "style: format CSS variables"
    
    # Maintenance
    '12': 'chore: update [dependency]',         # "chore: update React to v18"
    '13': 'chore: remove deprecated [code]',    # "chore: remove old analytics SDK"
    
    # Testing
    '14': 'test: add [type] test for [component]',  # "test: add unit tests for validation"
    '15': 'test: fix [test]',                       # "test: fix flaky API test"
    
    # CI/CD
    '16': 'ci: configure [pipeline]',           # "ci: configure Docker pipeline"
    '17': 'build: modify [config]',             # "build: modify webpack settings"
    
    # Special cases
    '18': 'revert: undo [change]',              # "revert: undo DB migration"
    '19': 'wip: [feature] in progress',         # "wip: shopping cart integration"
    '20': 'hotfix: emergency fix for [issue]'   # "hotfix: patch security vulnerability"
}

# ========== UTILITY FUNCTIONS ==========

def load_counters() -> Dict[str, int]:
    """Load commit counters from JSON file."""
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error reading counters file. Creating new one.")
    return {key: 0 for key in COMMIT_PURPOSES.keys()}

def save_counters(counters: Dict[str, int]) -> None:
    """Save commit counters to JSON file."""
    with open(COUNTER_FILE, 'w') as f:
        json.dump(counters, f, indent=2)

def run_git_command(command: str) -> Tuple[bool, str, str]:
    """Execute git command and return (success, stdout, stderr)."""
    process = subprocess.Popen(
        command,
        cwd=REPO_PATH,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode == 0, stdout.strip(), stderr.strip()

def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes."""
    success, stdout, _ = run_git_command("git status --porcelain")
    return success and stdout != ""

def get_current_branch() -> Optional[str]:
    """Get current git branch name."""
    success, stdout, _ = run_git_command("git branch --show-current")
    return stdout if success else None

def show_git_status() -> None:
    """Display git status information."""
    print("\n" + "="*50)
    print("GIT STATUS".center(50))
    print("="*50)
    
    # Show current branch
    branch = get_current_branch()
    print(f"Current branch: {branch or 'Unknown'}")
    
    # Show status
    _, status_output, _ = run_git_command("git status")
    print(f"\n{status_output}")
    
    # Show recent commits
    print("\nRecent commits:")
    _, log_output, _ = run_git_command("git log --oneline -5")
    print(log_output)
    
    print("="*50 + "\n")

def confirm_branch(target_branch: str) -> bool:
    """Confirm if user wants to use current branch."""
    current_branch = get_current_branch()
    if current_branch != target_branch:
        print(f"⚠️ You're not on '{target_branch}'. Current branch: '{current_branch}'")
        choice = input(f"Continue with '{current_branch}'? (y/N): ").lower()
        return choice == 'y'
    return True

def commit_and_push() -> None:
    """Interactive commit and push workflow."""
    counters = load_counters()
    
    # Show commit purpose options
    print("\n" + "="*50)
    print("SELECT COMMIT TYPE".center(50))
    print("="*50)
    for key, purpose in COMMIT_PURPOSES.items():
        print(f"{key.rjust(2)}: {purpose}")
    print("="*50)
    
    # Get user selection
    while True:
        choice = input("\nEnter commit type number (1-20) or 'c' to cancel: ").strip()
        if choice.lower() == 'c':
            print("Commit cancelled.")
            return
        if choice in COMMIT_PURPOSES:
            break
        print("Invalid choice. Please try again.")
    
    # Confirm branch
    if not confirm_branch(DEFAULT_BRANCH):
        return
    
    # Generate commit message
    counters[choice] += 1
    base_message = COMMIT_PURPOSES[choice]
    custom_part = input(f"\nComplete the message '{base_message}': ").strip()
    commit_message = f"{base_message.replace('[', '').replace(']', '')} {custom_part} (#{counters[choice]})"
    
    print(f"\nCommit message: {commit_message}")
    
    # Check for changes
    if not has_uncommitted_changes():
        print("No changes to commit.")
        return
    
    # Add and commit
    run_git_command("git add .")
    success, _, err = run_git_command(f'git commit -m "{commit_message}"')
    if not success:
        print(f"❌ Commit failed: {err}")
        return
    
    # Push changes
    print("\nPushing changes...")
    success, out, err = run_git_command("git push")
    if not success:
        if "no upstream branch" in err.lower():
            print(f"Setting upstream for branch...")
            branch = get_current_branch()
            success, _, _ = run_git_command(f"git push --set-upstream origin {branch}")
            if success:
                print(f"✅ Successfully set upstream and pushed to {branch}")
        else:
            print(f"❌ Push failed: {err}")
    else:
        print(f"✅ Successfully pushed changes")
    
    save_counters(counters)

# ========== MAIN MENU ==========

def main_menu() -> None:
    """Main interactive menu."""
    while True:
        print("\n" + "="*50)
        print("GIT HELPER TOOL".center(50))
        print("="*50)
        print("1. View Git Status")
        print("2. Commit & Push Changes")
        print("3. Exit")
        print("="*50)
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            show_git_status()
        elif choice == '2':
            commit_and_push()
        elif choice == '3':
            print("\nExiting Git Helper. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

# ========== ENTRY POINT ==========

if __name__ == "__main__":
    try:
        # Verify git repository
        if not os.path.exists(os.path.join(REPO_PATH, '.git')):
            print(f"❌ Error: {REPO_PATH} is not a Git repository")
            exit(1)
            
        main_menu()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")