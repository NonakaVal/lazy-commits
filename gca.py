#!/usr/bin/env python3
import subprocess
from datetime import datetime
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_PATH = "/usr/local/bin/gca"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

COMMIT_OPTIONS = {
    'update': ["small page fix", "section changed", "page content", "page content removed", "page content added", "full page and styles"],
    'feat':   ['add new feature', 'create component', 'integrate API'],
    'fix':    ['fix bug', 'resolve performance', 'adjust', 'critical error'],
    'docs':   ['update documentation', 'add examples', 'fix typo', 'add comments', "update readme"],
    'refactor': ['improve code', 'optimize', 'remove duplicate', 'simplify'],
    'chore':  ['update dependencies', 'configure environment', 'adjust settings', 'clean up old code'],
}

# ── .env ─────────────────────────────────────────────────────────────────────

def load_env_file():
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".config" / "gca" / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value

load_env_file()

OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# ── helpers ──────────────────────────────────────────────────────────────────

def run_command(command: list[str], show_error=True) -> bool:
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        if show_error:
            print(f"\n❌ Error: {e}")
        return False

def get_command_output(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def select_option(prompt: str, options: list[str], allow_quit=False):
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"  {i}: {option}")

    suffix = " (or 'q' to quit): " if allow_quit else ": "
    choice = input("\nEnter number" + suffix).strip().lower()

    if allow_quit and choice == 'q':
        return None

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(options):
            return idx - 1

    print("⚠️  Invalid choice. Defaulting to last option.")
    return len(options) - 1

def generate_commit_message(commit_type: str, message_part: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{commit_type}: {message_part} ({timestamp})"

def clean_ai_message(message: str) -> str:
    message = message.strip()
    message = message.replace("`", "")
    message = message.replace('"', "")
    message = message.replace("'", "")

    allowed_types = tuple(COMMIT_OPTIONS.keys())
    has_valid_type = any(message.startswith(t + ":") for t in allowed_types)

    if not has_valid_type:
        message = "update: " + message

    return message.strip()

# ── git diff ─────────────────────────────────────────────────────────────────

def get_git_diff_for_ai() -> str:
    staged_diff = get_command_output(['git', 'diff', '--cached'])
    unstaged_diff = get_command_output(['git', 'diff'])

    diff = ""

    if staged_diff:
        diff += "\n# STAGED DIFF\n"
        diff += staged_diff

    if unstaged_diff:
        diff += "\n# UNSTAGED DIFF\n"
        diff += unstaged_diff

    return diff.strip()

def get_git_summary_for_ai() -> str:
    status = get_command_output(['git', 'status', '--short'])
    name_status = get_command_output(['git', 'diff', '--name-status'])
    staged_name_status = get_command_output(['git', 'diff', '--cached', '--name-status'])

    summary = ""

    if status:
        summary += "\n# GIT STATUS\n" + status

    if staged_name_status:
        summary += "\n\n# STAGED FILES\n" + staged_name_status

    if name_status:
        summary += "\n\n# CHANGED FILES\n" + name_status

    return summary.strip()

# ── openrouter ai ────────────────────────────────────────────────────────────

def generate_ai_commit_message() -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("\n❌ OPENROUTER_API_KEY not found.")
        print("Create a .env file in this project or in ~/.config/gca/.env")
        print("\nExample:")
        print("OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx")
        print("OPENROUTER_MODEL=openai/gpt-4o-mini")
        return None

    diff = get_git_diff_for_ai()
    summary = get_git_summary_for_ai()

    if not diff and not summary:
        print("\n⚠️ No changes found.")
        return None

    max_diff_chars = 12000
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + "\n\n# DIFF TRUNCATED"

    prompt = f"""
Generate a concise git commit message based on the changes below.

Rules:
- Return only one commit message.
- Use this format: type: short message
- Valid types: update, feat, fix, docs, refactor, chore
- Do not use markdown.
- Do not use quotes.
- Keep it short and clear.
- Prefer English.

Git summary:
{summary}

Git diff:
{diff}
""".strip()

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You generate clean, concise git commit messages."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 80
    }

    request = urllib.request.Request(
        OPENROUTER_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "GCA Git Commit Assistant"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            message = data["choices"][0]["message"]["content"]
            return clean_ai_message(message)

    except urllib.error.HTTPError as e:
        print(f"\n❌ OpenRouter HTTP error: {e.code}")
        print(e.read().decode("utf-8", errors="ignore"))
        return None

    except urllib.error.URLError as e:
        print(f"\n❌ OpenRouter connection error: {e}")
        return None

    except Exception as e:
        print(f"\n❌ AI generation failed: {e}")
        return None

# ── commit flow ───────────────────────────────────────────────────────────────

def commit_changes(message: str):
    print(f"\nGenerated commit message:\n  🔸 {message}")

    if input("\nConfirm commit? (y/n): ").lower().strip() != 'y':
        print("\n❌ Commit canceled")
        return

    if run_command(['git', 'add', '.']) and run_command(['git', 'commit', '-m', message]):
        print("\n✅ Commit successful!")

        if input("Push to remote? (y/n): ").lower().strip() == 'y':
            if run_command(['git', 'push']):
                print("\n🚀 Successfully pushed to remote!")
            else:
                print("\n❌ Push failed")

def create_custom_commit():
    print("\nEnter your commit message:")
    custom_msg = input("Message: ").strip()

    commit_type = "chore"

    for t in COMMIT_OPTIONS:
        if custom_msg.lower().startswith(t + ":"):
            commit_type = t
            custom_msg = custom_msg[len(t)+1:].strip()
            break

    commit_changes(generate_commit_message(commit_type, custom_msg))

def guided_commit():
    types = list(COMMIT_OPTIONS.keys())
    type_index = select_option("SELECT commit type:", types, allow_quit=True)

    if type_index is None:
        return

    commit_type = types[type_index]
    msg_options = COMMIT_OPTIONS[commit_type]
    msg_index = select_option(f"SELECT message ({commit_type}):", msg_options)

    commit_changes(generate_commit_message(commit_type, msg_options[msg_index]))

def ai_commit():
    print("\n🤖 Generating commit message with AI...")
    message = generate_ai_commit_message()

    if not message:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"{message} ({timestamp})"

    commit_changes(message)

def create_commit_flow():
    print("\n  1: Guided commit (select from options)")
    print("  2: Custom commit message")
    print("  3: AI commit message using OpenRouter")
    print("  q: Cancel")

    choice = input("\nSelect: ").strip().lower()

    if choice == '1':
        guided_commit()
    elif choice == '2':
        create_custom_commit()
    elif choice == '3':
        ai_commit()

# ── edit self ─────────────────────────────────────────────────────────────────

def edit_script():
    editors = ['nano', 'vim', 'vi', 'gedit', 'code']
    editor = None

    for e in editors:
        if subprocess.run(['which', e], capture_output=True).returncode == 0:
            editor = e
            break

    if not editor:
        print("❌ No editor found (nano, vim, gedit, code).")
        return

    print(f"\n📝 Opening {SCRIPT_PATH} with {editor}...")
    subprocess.run([editor, SCRIPT_PATH])

# ── git status ────────────────────────────────────────────────────────────────

def show_status():
    print()
    subprocess.run(['git', 'status', '--short'])
    print()

# ── main ──────────────────────────────────────────────────────────────────────

def check_git_repo():
    if not os.path.exists(".git"):
        print("❌ Not a git repository. Navigate to a project folder first.")
        sys.exit(1)

def main():
    check_git_repo()

    print("\n🐙 Git Commit Assistant")
    print(f"   📁 {os.getcwd()}")
    print(f"   🤖 Model: {OPENROUTER_MODEL}")

    while True:
        show_status()

        print("  1: New commit")
        print("  2: Edit this script (gca)")
        print("  3: Exit")

        choice = input("\nSelect: ").strip()

        if choice == '1':
            create_commit_flow()
        elif choice == '2':
            edit_script()
        elif choice == '3':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()