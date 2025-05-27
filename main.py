import subprocess
import os
import re
from collections import defaultdict
import json
from datetime import datetime
import sys
from typing import Dict, List, Optional, Set, Tuple

# Constants
REPO_PATH = r"C:\Users\desktop\Documents\MyApps\lazy-commits"
DEFAULT_BRANCH = "main"
COUNTERS_FILE = os.path.join(REPO_PATH, '.commit_counters.json')
CONFIG_FILE = os.path.join(REPO_PATH, '.commit_assistant_config.json')
MAX_SUGGESTIONS = 5
MAX_RECENT_COMMITS = 10

# Color codes for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

class GitAssistant:
    def __init__(self):
        self.repo_path = REPO_PATH
        self.default_branch = DEFAULT_BRANCH
        self.counters_file = COUNTERS_FILE
        self.config_file = CONFIG_FILE
        self.commit_purposes = self.load_commit_templates()
        self.recent_commits = []
        self.load_config()

    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            'frequent_terms': {},
            'recent_components': [],
            'custom_templates': {},
            'preferred_branch': DEFAULT_BRANCH
        }
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with default config in case new keys were added
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def load_commit_templates(self) -> Dict[str, List[str]]:
        """Load commit message templates with customization support"""
        default_templates = {
            'fix': [
                'fix: correct typo in [component]',
                'fix: resolve [issue] in [component]',
                'fix: repair broken [functionality]',
                'fix: adjust UI layout in [component]',
                'fix: fix broken links in [file]'
            ],
            'feat': [
                'feat: implement [feature]',
                'feat: add [component] to [section]',
                'feat: integrate [service/api]',
                'feat: improve search in [module]',
                'feat: add validation to [form]'
            ],
            'docs': [
                'docs: update [document]',
                'docs: add examples for [feature]',
                'docs: update README',
                'docs: add comments in [file]'
            ],
            'refactor': [
                'refactor: simplify [component]',
                'refactor: restructure [module]',
                'refactor: clean redundant code in [file]'
            ],
            'perf': [
                'perf: optimize [process]',
                'perf: improve performance of [component]'
            ],
            'style': [
                'style: format [file/component]',
                'style: update UI details in [module]'
            ],
            'chore': [
                'chore: update [dependency]',
                'chore: remove deprecated [code]',
                'chore: clean files in [folder]',
                'chore: update environment config'
            ],
            'test': [
                'test: add [type] test for [component]',
                'test: fix flaky [test]'
            ],
            'ci': [
                'ci: configure [pipeline]',
                'ci: update workflows'
            ],
            'build': [
                'build: modify [config]',
                'build: update build config for [platform]'
            ],
            'revert': [
                'revert: undo [change]'
            ],
            'wip': [
                'wip: [feature] in progress'
            ]
        }
        
        # Check for custom templates in config
        if hasattr(self, 'config') and 'custom_templates' in self.config:
            for category, templates in self.config['custom_templates'].items():
                if category in default_templates:
                    default_templates[category].extend(templates)
                else:
                    default_templates[category] = templates
        
        return default_templates

    def load_counters(self) -> Dict[str, int]:
        """Load commit counters from file"""
        try:
            with open(self.counters_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return defaultdict(int)

    def save_counters(self, counters: Dict[str, int]):
        """Save commit counters to file"""
        with open(self.counters_file, 'w') as f:
            json.dump(counters, f, indent=2)

    def run_git_command(self, command: str, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Execute a git command and return the result"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                shell=True,
                text=True,
                capture_output=capture_output
            )
            
            if result.returncode != 0 and capture_output:
                self.print_error(f"Error executing '{command}': {result.stderr}")
            elif capture_output and result.stdout:
                self.print_success(result.stdout)
            
            return result
        except Exception as e:
            self.print_error(f"Failed to execute command: {e}")
            return subprocess.CompletedProcess(command, 1, stderr=str(e))

    def print_error(self, message: str):
        """Print error message with formatting"""
        print(f"{COLORS['FAIL']}❌ {message}{COLORS['ENDC']}")

    def print_success(self, message: str):
        """Print success message with formatting"""
        print(f"{COLORS['OKGREEN']}✅ {message}{COLORS['ENDC']}")

    def print_warning(self, message: str):
        """Print warning message with formatting"""
        print(f"{COLORS['WARNING']}⚠️ {message}{COLORS['ENDC']}")

    def print_info(self, message: str):
        """Print info message with formatting"""
        print(f"{COLORS['OKBLUE']}ℹ️ {message}{COLORS['ENDC']}")

    def has_changes(self) -> bool:
        """Check if there are changes to commit"""
        result = self.run_git_command('git status --porcelain')
        return bool(result.stdout.strip())

    def get_changed_files(self) -> List[str]:
        """Get list of modified files"""
        result = self.run_git_command('git diff --name-only HEAD')
        if result.returncode != 0 or not result.stdout:
            return []
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]

    def analyze_changes(self) -> Dict:
        """Analyze changes to suggest components and terms"""
        changed_files = self.get_changed_files()
        components: Set[str] = set()
        terms: Dict[str, int] = defaultdict(int)
        file_extensions: Dict[str, int] = defaultdict(int)
        
        for file_path in changed_files:
            # Extract filename without extension
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            if file_name:
                components.add(file_name)
            
            # Extract file extension
            _, ext = os.path.splitext(file_path)
            if ext:
                file_extensions[ext.lower()] += 1
            
            # Extract terms from file path
            dir_parts = os.path.dirname(file_path).replace('\\', '/').split('/')
            for part in dir_parts:
                if part and not part.startswith('.'):
                    # Split camelCase and snake_case
                    split_parts = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', part)).split()
                    for sub_part in split_parts:
                        if '_' in sub_part:
                            split_parts.extend(sub_part.split('_'))
                    
                    for term in split_parts:
                        if len(term) > 2:  # Ignore very short terms
                            terms[term.lower()] += 1
        
        # Update frequent terms in config
        for term, count in terms.items():
            self.config['frequent_terms'][term] = self.config['frequent_terms'].get(term, 0) + count
        
        # Sort terms by frequency (existing + new)
        sorted_terms = sorted(
            self.config['frequent_terms'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get most common file type
        primary_file_type = max(file_extensions.items(), key=lambda x: x[1], default=('', 0))[0]
        
        return {
            'components': list(components),
            'top_terms': [term[0] for term in sorted_terms[:3]] if sorted_terms else [],
            'changed_files': changed_files,
            'file_types': dict(file_extensions),
            'primary_file_type': primary_file_type
        }

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        result = self.run_git_command('git branch --show-current')
        return result.stdout.strip() if result.returncode == 0 else None

    def confirm_branch(self, suggested_branch: str) -> Optional[str]:
        """Confirm or change the current branch"""
        current_branch = self.get_current_branch()
        if not current_branch:
            self.print_error("Could not determine current branch.")
            return None
        
        self.print_info(f"Current branch: {current_branch}")
        change = input("Keep this branch? (y/n): ").strip().lower()
        
        if change == 'n':
            new_branch = input("Enter new branch name: ").strip()
            if new_branch:
                result = self.run_git_command(f'git checkout -b {new_branch}')
                if result.returncode == 0:
                    return new_branch
                return None
            return None
        return current_branch

    def get_placeholder_replacements(self, analysis: Dict) -> Dict[str, str]:
        """Generate replacements for commit message placeholders"""
        components = analysis['components']
        top_terms = analysis['top_terms']
        changed_files = analysis['changed_files']
        file_types = analysis['file_types']
        
        replacements = {
            '[component]': components[0] if components else 'component',
            '[file]': os.path.basename(changed_files[0]) if changed_files else 'file',
            '[module]': top_terms[0] if top_terms else 'module',
            '[feature]': top_terms[0] if top_terms else 'feature',
            '[section]': top_terms[1] if len(top_terms) > 1 else 'section',
            '[form]': top_terms[0] if top_terms else 'form',
            '[functionality]': top_terms[0] if top_terms else 'functionality',
            '[process]': top_terms[0] if top_terms else 'process',
            '[dependency]': top_terms[0] if top_terms else 'dependency',
            '[folder]': top_terms[0] if top_terms else 'folder',
            '[test]': top_terms[0] if top_terms else 'test',
            '[pipeline]': top_terms[0] if top_terms else 'pipeline',
            '[platform]': top_terms[0] if top_terms else 'platform',
            '[change]': top_terms[0] if top_terms else 'change',
            '[document]': top_terms[0] if top_terms else 'document',
            '[issue]': 'issue',
            '[filetype]': analysis['primary_file_type'] if analysis['primary_file_type'] else 'file',
            '[service/api]': top_terms[0] if top_terms else 'API'
        }
        
        # Add numbered components if multiple exist
        for i, component in enumerate(components[:3], 1):
            replacements[f'[component{i}]'] = component
        
        return replacements

    def replace_placeholders(self, template: str, analysis: Dict) -> str:
        """Replace placeholders in commit message with suggestions"""
        replacements = self.get_placeholder_replacements(analysis)
        
        for placeholder, replacement in replacements.items():
            template = template.replace(placeholder, replacement)
        
        return template

    def show_git_commands_menu(self):
        """Show additional Git commands menu"""
        while True:
            print(f"\n{COLORS['HEADER']}🔧 Additional Git Commands:{COLORS['ENDC']}")
            print("1: git pull")
            print("2: git branch -a (list all branches)")
            print("3: git status")
            print(f"4: git log --oneline -{MAX_RECENT_COMMITS} (recent commits)")
            print("5: git diff (show changes)")
            print("6: git stash (stash changes)")
            print("7: git fetch (fetch updates)")
            print("8: Custom git command")
            print("0: Back to main menu")
            
            choice = input("Choose an option: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.run_git_command('git pull')
            elif choice == '2':
                self.run_git_command('git branch -a')
            elif choice == '3':
                self.run_git_command('git status')
            elif choice == '4':
                self.run_git_command(f'git log --oneline -{MAX_RECENT_COMMITS}')
            elif choice == '5':
                self.run_git_command('git diff --color')
            elif choice == '6':
                message = input("Stash message (optional): ").strip()
                cmd = 'git stash' + (f' -m "{message}"' if message else '')
                self.run_git_command(cmd)
            elif choice == '7':
                self.run_git_command('git fetch')
            elif choice == '8':
                custom_cmd = input("Enter full git command: ").strip()
                if custom_cmd.startswith('git '):
                    self.run_git_command(custom_cmd)
                else:
                    self.print_error("For security, only git commands are allowed.")
            else:
                self.print_error("Invalid option")

    def suggest_commit_message(self, category: str, analysis: Dict) -> Optional[str]:
        """Suggest commit message based on category and changes"""
        if category not in self.commit_purposes:
            self.print_error(f"Invalid category: {category}")
            return None
        
        variations = self.commit_purposes[category]
        
        print(f"\n{COLORS['HEADER']}✍️ {category.upper()} Message Variations:{COLORS['ENDC']}")
        for idx, variation in enumerate(variations[:MAX_SUGGESTIONS], 1):
            preview = self.replace_placeholders(variation, analysis)
            print(f"{idx}: {preview}")
        
        if len(variations) > MAX_SUGGESTIONS:
            print(f"... and {len(variations) - MAX_SUGGESTIONS} more")
        
        print(f"\n{COLORS['OKBLUE']}c: Cancel")
        print("n: New custom message")
        print("e: Edit existing template{COLORS['ENDC']}")
        
        choice = input("\nChoose variation: ").strip().lower()
        
        if choice == 'c':
            self.print_warning("Operation canceled.")
            return None
        elif choice == 'n':
            return input("Enter custom commit message: ").strip()
        elif choice == 'e':
            return self.edit_commit_template(category, analysis)
        elif choice.isdigit() and 1 <= int(choice) <= len(variations):
            return variations[int(choice) - 1]
        else:
            self.print_error("Invalid selection")
            return None

    def edit_commit_template(self, category: str, analysis: Dict) -> Optional[str]:
        """Edit an existing commit template"""
        if category not in self.commit_purposes:
            self.print_error(f"Invalid category: {category}")
            return None
        
        variations = self.commit_purposes[category]
        
        print(f"\n{COLORS['HEADER']}Edit Template for {category.upper()}:{COLORS['ENDC']}")
        for idx, variation in enumerate(variations[:MAX_SUGGESTIONS], 1):
            print(f"{idx}: {variation}")
        
        choice = input("\nSelect template to edit (or 'c' to cancel): ").strip().lower()
        
        if choice == 'c':
            return None
        elif choice.isdigit() and 1 <= int(choice) <= len(variations):
            index = int(choice) - 1
            current = variations[index]
            print(f"\nCurrent template: {current}")
            new_template = input("Enter new template: ").strip()
            
            if new_template:
                # Save to custom templates in config
                if 'custom_templates' not in self.config:
                    self.config['custom_templates'] = {}
                
                if category not in self.config['custom_templates']:
                    self.config['custom_templates'][category] = []
                
                self.config['custom_templates'][category].append(new_template)
                self.save_config()
                self.commit_purposes = self.load_commit_templates()  # Reload templates
                
                self.print_success("Template saved! It will be available next time.")
                return new_template
            return None
        else:
            self.print_error("Invalid selection")
            return None

    def show_changes_summary(self, analysis: Dict):
        """Show summary of changes"""
        changed_files = analysis['changed_files']
        
        print(f"\n{COLORS['HEADER']}📋 Detected Changes:{COLORS['ENDC']}")
        if changed_files:
            # Group by directory
            file_groups = defaultdict(list)
            for file in changed_files:
                dirname = os.path.dirname(file) or '.'
                file_groups[dirname].append(os.path.basename(file))
            
            for dirname, files in file_groups.items():
                print(f"\n{COLORS['UNDERLINE']}{dirname}/{COLORS['ENDC']}")
                for file in files[:5]:
                    print(f"- {file}")
                if len(files) > 5:
                    print(f"- ... and {len(files) - 5} more")
            
            print(f"\n{COLORS['OKBLUE']}Total files changed: {len(changed_files)}{COLORS['ENDC']}")
            
            if analysis['file_types']:
                print("\nFile types modified:")
                for ext, count in analysis['file_types'].items():
                    print(f"- {ext}: {count} files")
        else:
            self.print_warning("No changes detected.")

    def execute_commit_flow(self):
        """Execute the smart commit flow"""
        if not self.has_changes():
            self.print_warning("No changes to commit.")
            return
        
        counters = self.load_counters()
        analysis = self.analyze_changes()
        
        print(f"\n{COLORS['HEADER']}📜 Commit Categories:{COLORS['ENDC']}")
        keys = list(self.commit_purposes.keys())
        for idx, key in enumerate(keys, 1):
            print(f"{idx}: {key.upper()}")
        
        print(f"\n{COLORS['OKBLUE']}c: Cancel")
        print("a: Analyze changes in detail{COLORS['ENDC']}")
        
        category_choice = input("\nSelect category: ").strip().lower()
        
        if category_choice == 'c':
            self.print_warning("Operation canceled.")
            return
        elif category_choice == 'a':
            self.show_changes_summary(analysis)
            return self.execute_commit_flow()  # Show menu again
        
        if not category_choice.isdigit() or not (1 <= int(category_choice) <= len(keys)):
            self.print_error("Invalid category.")
            return
        
        category_key = keys[int(category_choice) - 1]
        commit_message = self.suggest_commit_message(category_key, analysis)
        
        if not commit_message:
            return
        
        branch = self.confirm_branch(self.default_branch)
        if branch is None:
            return
        
        # Generate version counter key
        key_id = f"{category_key}-{datetime.now().strftime('%Y%m%d')}"
        counters[key_id] = counters.get(key_id, 0) + 1
        
        # Replace placeholders and add version
        final_message = self.replace_placeholders(commit_message, analysis)
        final_message = f"{final_message} (v{counters[key_id]})"
        
        print(f"\n{COLORS['HEADER']}📝 Commit Message:{COLORS['ENDC']}")
        print(final_message)
        
        edit = input("\nEdit message? (y/n): ").strip().lower()
        if edit == 'y':
            final_message = input("Enter new message: ").strip()
        
        self.show_changes_summary(analysis)
        
        if not self.has_changes():
            self.print_warning("No changes to commit.")
            return
        
        confirm = input("\nConfirm commit? (y/n): ").strip().lower()
        if confirm != 'y':
            self.print_warning("Operation canceled.")
            return
        
        # Stage all changes
        self.run_git_command('git add .')
        
        # Commit
        commit_result = self.run_git_command(f'git commit -m "{final_message}"')
        if commit_result.returncode != 0:
            self.print_error("Commit failed.")
            return
        
        # Push
        push_result = self.run_git_command('git push')
        
        if 'has no upstream branch' in push_result.stderr:
            self.print_info(f"Branch '{branch}' has no upstream. Configuring...")
            self.run_git_command(f'git push --set-upstream origin {branch}')
            self.print_success(f"Upstream configured: 'origin/{branch}'")
        elif push_result.returncode != 0:
            self.print_error(f"Push failed: {push_result.stderr}")
        else:
            self.print_success(f"Successfully pushed to '{branch}'!")
        
        self.save_counters(counters)
        
        # Add to recent commits
        self.recent_commits.append({
            'message': final_message,
            'branch': branch,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.recent_commits) > MAX_RECENT_COMMITS:
            self.recent_commits.pop(0)

    def show_main_menu(self):
        """Show the main menu"""
        while True:
            print(f"\n{COLORS['HEADER']}🌿 Git Assistant Main Menu:{COLORS['ENDC']}")
            print("1: Smart Commit & Push")
            print("2: Additional Git Commands")
            print("3: View Recent Commits")
            print("4: Configure Settings")
            print("0: Exit")
            
            choice = input("Choose an option: ").strip()
            
            if choice == '0':
                self.print_info("Goodbye! 👋")
                break
            elif choice == '1':
                self.execute_commit_flow()
            elif choice == '2':
                self.show_git_commands_menu()
            elif choice == '3':
                self.show_recent_commits()
            elif choice == '4':
                self.configure_settings()
            else:
                self.print_error("Invalid option")

    def show_recent_commits(self):
        """Show recent commits history"""
        if not self.recent_commits:
            self.print_info("No recent commits recorded.")
            return
        
        print(f"\n{COLORS['HEADER']}⏳ Recent Commits:{COLORS['ENDC']}")
        for idx, commit in enumerate(reversed(self.recent_commits), 1):
            print(f"\n{idx}. {commit['message']}")
            print(f"   Branch: {commit['branch']}")
            print(f"   Time: {commit['timestamp']}")

    def configure_settings(self):
        """Configure assistant settings"""
        while True:
            print(f"\n{COLORS['HEADER']}⚙️ Configuration:{COLORS['ENDC']}")
            print("1: Change default branch (current: {self.default_branch})")
            print("2: View frequent terms")
            print("3: Reset configuration")
            print("0: Back to main menu")
            
            choice = input("Choose an option: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                new_branch = input("Enter new default branch: ").strip()
                if new_branch:
                    self.default_branch = new_branch
                    self.config['preferred_branch'] = new_branch
                    self.save_config()
                    self.print_success("Default branch updated!")
            elif choice == '2':
                self.show_frequent_terms()
            elif choice == '3':
                self.reset_configuration()
            else:
                self.print_error("Invalid option")

    def show_frequent_terms(self):
        """Show frequently used terms"""
        if not self.config['frequent_terms']:
            self.print_info("No frequent terms recorded yet.")
            return
        
        print(f"\n{COLORS['HEADER']}📊 Frequent Terms:{COLORS['ENDC']}")
        sorted_terms = sorted(
            self.config['frequent_terms'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for term, count in sorted_terms[:20]:
            print(f"- {term}: {count} uses")

    def reset_configuration(self):
        """Reset configuration to defaults"""
        confirm = input("Are you sure you want to reset all configuration? (y/n): ").strip().lower()
        if confirm == 'y':
            self.config = {
                'frequent_terms': {},
                'recent_components': [],
                'custom_templates': {},
                'preferred_branch': DEFAULT_BRANCH
            }
            self.save_config()
            self.commit_purposes = self.load_commit_templates()
            self.print_success("Configuration reset to defaults!")


if __name__ == "__main__":
    try:
        assistant = GitAssistant()
        assistant.show_main_menu()
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n{COLORS['FAIL']}⚠️ An error occurred: {e}{COLORS['ENDC']}")
        sys.exit(1)