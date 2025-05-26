import subprocess
import os
import json

# ========== CONFIGURAÇÕES ==========
repo_path = r'C:\Users\desktop\Documents\MyApps\lazy-commits'  # Caminho do seu repositório
default_branch = 'main'  # Branch padrão




commit_purposes = {
    # FIXES (Correções de bugs/erros - gera PATCH version semântica)
    '1': 'fix: correct typo in [component]',  # Ex: "fix: correct typo in login error message"
    '2': 'fix: resolve [issue] in [component]',  # Ex: "fix: resolve infinite loop in data parser"
    '3': 'fix: repair broken [functionality]',  # Ex: "fix: repair broken image upload"
    
    # FEATURES (Novas funcionalidades - gera MINOR version)
    '4': 'feat: implement [feature]',  # Ex: "feat: implement dark mode toggle"
    '5': 'feat: add [component] to [section]',  # Ex: "feat: add pagination to user dashboard"
    '6': 'feat: integrate [service/api]',  # Ex: "feat: integrate Stripe payment gateway"
    
    # DOCS (Documentação - não afeta versão)
    '7': 'docs: update [document]',  # Ex: "docs: update API endpoint documentation"
    '8': 'docs: add examples for [feature]',  # Ex: "docs: add examples for auth middleware"
    
    # CODE QUALITY (Melhorias de código)
    '9': 'refactor: simplify [component]',  # Ex: "refactor: simplify cart calculation logic"
    '10': 'perf: optimize [process]',  # Ex: "perf: optimize image compression algorithm"
    '11': 'style: format [file/component]',  # Ex: "style: format CSS variables"
    
    # CHORES (Tarefas de manutenção)
    '12': 'chore: update [dependency]',  # Ex: "chore: update React to v18"
    '13': 'chore: remove deprecated [code]',  # Ex: "chore: remove deprecated analytics SDK"
    
    # TESTING
    '14': 'test: add [type] test for [component]',  # Ex: "test: add unit tests for validation utils"
    '15': 'test: fix flaky [test]',  # Ex: "test: fix flaky API timeout test"
    
    # CI/CD & BUILD
    '16': 'ci: configure [pipeline]',  # Ex: "ci: configure Docker build pipeline"
    '17': 'build: modify [config]',  # Ex: "build: modify webpack output settings"
    
    # MENSAGENS ESPECIAIS
    '18': 'revert: undo [change]',  # Ex: "revert: undo experimental database migration"
    '19': 'wip: [feature] in progress',  # Ex: "wip: shopping cart integration"
}

counter_file = os.path.join(repo_path, 'commit_counters.json')

# ========== FUNÇÕES DE UTILIDADE ==========

def load_counters():
    """Carrega os contadores de commit do arquivo."""
    if os.path.exists(counter_file):
        with open(counter_file, 'r') as f:
            return json.load(f)
    else:
        return {key: 0 for key in commit_purposes.keys()}

def save_counters(counters):
    """Salva os contadores de commit no arquivo."""
    with open(counter_file, 'w') as f:
        json.dump(counters, f, indent=4)

def run_git_command(command, capture_output=False):
    """Executa um comando Git no repositório."""
    process = subprocess.Popen(
        command,
        cwd=repo_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    
    if capture_output:
        return process.returncode == 0, stdout.decode(), stderr.decode()
    
    if process.returncode == 0:
        print(stdout.decode())
    else:
        print(f"❌ Error: {stderr.decode()}")
    return process.returncode == 0

def has_changes():
    """Verifica se há alterações a serem commitadas."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo_path,
        capture_output=True,
        text=True,
        shell=True
    )
    return result.stdout.strip() != ""

def get_current_branch():
    """Obtém o nome da branch atual."""
    result = subprocess.run(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        cwd=repo_path,
        capture_output=True,
        text=True,
        shell=True
    )
    return result.stdout.strip()

def show_git_status():
    """Mostra o status do Git."""
    print("\n📊 Status do Git:")
    run_git_command('git status')
    print()

def confirm_branch(branch):
    """Confirma se o usuário deseja usar a branch atual."""
    current_branch = get_current_branch()
    if current_branch != branch:
        print(f"⚠️ Você não está na branch '{branch}'. Branch atual: '{current_branch}'")
        choice = input(f"Deseja continuar com a branch atual '{current_branch}'? (s/n): ").lower()
        if choice != 's':
            print("Operação cancelada.")
            return None
        return current_branch
    return branch

def git_commit_push():
    """Faz commit e push da branch atual."""
    counters = load_counters()

    print("\n📜 Selecione o propósito do commit:")
    for key, purpose in commit_purposes.items():
        print(f"{key}: {purpose}")
    
    purpose_key = input("Digite o número correspondente ao propósito (ou 'c' para cancelar): ").strip()

    if purpose_key.lower() == 'c':
        print("Operação cancelada.")
        return
    
    if purpose_key not in commit_purposes:
        print("❌ Seleção inválida.")
        return

    branch = confirm_branch(default_branch)
    if branch is None:
        return

    counters[purpose_key] += 1
    commit_message = f"{commit_purposes[purpose_key]} (#{counters[purpose_key]})"
    
    print(f"\n📝 Commit message: {commit_message}\n")
    
    if not has_changes():
        print("⚠️ Nenhuma alteração detectada. Nada para commit.")
        return

    run_git_command('git add .')
    run_git_command(f'git commit -m "{commit_message}"')

    result = subprocess.run(
        ['git', 'push'],
        cwd=repo_path,
        capture_output=True,
        text=True,
        shell=True
    )

    if 'has no upstream branch' in result.stderr:
        print(f"🔗 Branch '{branch}' não tem upstream. Configurando...")
        run_git_command(f'git push --set-upstream origin {branch}')
        print(f"✅ Upstream configurado: 'origin/{branch}'")
    elif result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
    else:
        print(f"✅ Push realizado com sucesso para '{branch}'!")
    
    save_counters(counters)

# ========== MENU PRINCIPAL ==========

def main_menu():
    """Exibe o menu principal e processa as escolhas do usuário."""
    while True:
        print("\n" + "="*40)
        print("MENU PRINCIPAL".center(40))
        print("="*40)
        print("1. Ver status do Git")
        print("2. Fazer commit e push")
        print("3. Encerrar programa")
        print("="*40)
        
        choice = input("Escolha uma opção (1-3): ").strip()
        
        if choice == '1':
            show_git_status()
        elif choice == '2':
            git_commit_push()
        elif choice == '3':
            print("Encerrando o programa...")
            break
        else:
            print("❌ Opção inválida. Por favor, escolha 1, 2 ou 3.")

# ========== EXECUÇÃO PRINCIPAL ==========

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")