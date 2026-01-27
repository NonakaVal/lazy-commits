#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

# ------------------------------
# Configuração de opções de commit
# ------------------------------
COMMIT_OPTIONS = {
    "update": ["minor update", "data update", "config update", "workflow update", "full update"],
    "vault": ["minor update", "adjust structure", "update config", "add templates", "new plugin setup", "content update", "full update"],
    "feat": ["new feature", "new component", "API integration", "automation"],
    "fix": ["bug fix", "performance fix", "error fix", "critical fix"],
    "docs": ["documentation", "add example", "readme update", "comment code"],
    "refactor": ["code improvement", "optimize", "simplify", "remove redundancy"],
    "chore": ["dependency update", "environment setup", "CI/CD update", "cleanup"]
}

# ------------------------------
# Funções auxiliares
# ------------------------------

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError:
        print(f"❌ Command failed: {cmd}")
        return False
    return True

def select_option(prompt, options, allow_quit=False):
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"{i}: {opt}")
    while True:
        choice = input("Enter number{}: ".format(" (or q to quit)" if allow_quit else ""))
        if allow_quit and choice.lower() == 'q':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        print("⚠️ Invalid choice, try again.")

def generate_commit_message(commit_type, message):
    return f"{commit_type}: {message} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

def commit_changes(message):
    print(f"\nGenerated commit message:\n🔸 {message}")
    confirm = input("Confirm commit? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ Commit canceled")
        return
    if run_command("git add .") and run_command(f'git commit -m "{message}"'):
        print("✅ Commit successful!")
        if input("Push to remote? (y/n): ").lower() == 'y':
            run_command("git push")

def create_custom_commit():
    custom_msg = input("Enter your commit message: ")
    commit_type = "chore"
    for t in COMMIT_OPTIONS.keys():
        if custom_msg.startswith(f"{t}:"):
            commit_type = t
            custom_msg = custom_msg[len(t)+1:].strip()
            break
    commit_changes(generate_commit_message(commit_type, custom_msg))

def create_commit_flow():
    print("\nChoose commit method:")
    print("1: Use guided commit")
    print("2: Write custom commit message")
    print("q: Cancel")
    choice = input("Select option: ")

    if choice == '1':
        types = list(COMMIT_OPTIONS.keys())
        idx = select_option("SELECT FIRST PART (commit type):", types, allow_quit=True)
        if idx is None:
            return
        commit_type = types[idx]
        messages = COMMIT_OPTIONS[commit_type]
        idx_msg = select_option(f"SELECT SECOND PART ({commit_type} options):", messages)
        message_part = messages[idx_msg]
        commit_changes(generate_commit_message(commit_type, message_part))
    elif choice == '2':
        create_custom_commit()
    elif choice.lower() == 'q':
        return
    else:
        print("⚠️ Invalid option")

def check_git_repo():
    if not os.path.isdir(".git"):
        print("❌ This is not a git repository")
        sys.exit(1)

def start_ssh_agent():
    # Start SSH agent and add key
    run_command('eval "$(ssh-agent -s)"')
    run_command("ssh-add ~/.ssh/id_ed25519")

# ------------------------------
# Main
# ------------------------------
def main():
    check_git_repo()
    start_ssh_agent()
    print("🐙 Git Commit Assistant")

    while True:
        print("\n1: Start new commit")
        print("2: Exit")
        user_input = input("Select option: ")
        if user_input == '1':
            create_commit_flow()
        elif user_input == '2':
            print("👋 Goodbye!")
            break
        else:
            print("⚠️ Invalid option, please try again")

if __name__ == "__main__":
    main()
