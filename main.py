import subprocess
import os
from collections import defaultdict
import json

# Configurações
repo_path = r"C:\Users\desktop\Documents\MyApps\lazy-commits"
default_branch = "main"
counters_file = os.path.join(repo_path, '.commit_counters.json')

# Tabela de variações de commit
commit_purposes = {
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
        'docs: improve README',
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

def load_counters():
    """Carrega os contadores de commits do arquivo."""
    try:
        with open(counters_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaultdict(int)

def save_counters(counters):
    """Salva os contadores de commits no arquivo."""
    with open(counters_file, 'w') as f:
        json.dump(counters, f)

def run_git_command(command):
    """Executa um comando git e retorna o resultado."""
    result = subprocess.run(command, cwd=repo_path, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"⚠️ Erro ao executar '{command}': {result.stderr}")
    else:
        print(result.stdout)
    return result

def has_changes():
    """Verifica se há alterações para commit."""
    result = run_git_command('git status --porcelain')
    return bool(result.stdout.strip())

def get_changed_files():
    """Retorna a lista de arquivos modificados."""
    result = run_git_command('git diff --name-only HEAD')
    if result.returncode != 0 or not result.stdout:
        return []
    return [f.strip() for f in result.stdout.split('\n') if f.strip()]

def analyze_changes():
    """Analisa as alterações para sugerir componentes e termos."""
    changed_files = get_changed_files()
    components = set()
    terms = defaultdict(int)
    
    for file_path in changed_files:
        # Extrai nome do arquivo sem extensão
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if file_name:
            components.add(file_name)
        
        # Extrai termos do caminho do arquivo
        dir_parts = os.path.dirname(file_path).split('/')
        for part in dir_parts:
            if part and not part.startswith('.'):
                terms[part] += 1
    
    # Ordena termos por frequência
    sorted_terms = sorted(terms.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'components': list(components),
        'top_terms': [term[0] for term in sorted_terms[:3]] if sorted_terms else [],
        'changed_files': changed_files
    }

def confirm_branch(suggested_branch):
    """Confirma ou permite alterar o branch atual."""
    current_branch = run_git_command('git branch --show-current').stdout.strip()
    if not current_branch:
        print("❌ Não foi possível determinar o branch atual.")
        return None
    
    print(f"\n🌿 Branch atual: {current_branch}")
    change = input("Manter este branch? (s/n): ").strip().lower()
    
    if change == 'n':
        new_branch = input("Digite o nome do novo branch: ").strip()
        if new_branch:
            result = run_git_command(f'git checkout -b {new_branch}')
            if result.returncode == 0:
                return new_branch
            return None
        return None
    return current_branch

def replace_placeholders(template, analysis):
    """Substitui placeholders na mensagem de commit com sugestões."""
    placeholders = {
        '[component]': analysis['components'][0] if analysis['components'] else 'component',
        '[file]': os.path.basename(analysis['changed_files'][0]) if analysis['changed_files'] else 'file',
        '[module]': analysis['top_terms'][0] if analysis['top_terms'] else 'module',
        '[feature]': analysis['top_terms'][0] if analysis['top_terms'] else 'feature',
        '[section]': analysis['top_terms'][1] if len(analysis['top_terms']) > 1 else 'section',
        '[form]': analysis['top_terms'][0] if analysis['top_terms'] else 'form',
        '[functionality]': analysis['top_terms'][0] if analysis['top_terms'] else 'functionality',
        '[process]': analysis['top_terms'][0] if analysis['top_terms'] else 'process',
        '[dependency]': analysis['top_terms'][0] if analysis['top_terms'] else 'dependency',
        '[folder]': analysis['top_terms'][0] if analysis['top_terms'] else 'folder',
        '[test]': analysis['top_terms'][0] if analysis['top_terms'] else 'test',
        '[pipeline]': analysis['top_terms'][0] if analysis['top_terms'] else 'pipeline',
        '[platform]': analysis['top_terms'][0] if analysis['top_terms'] else 'platform',
        '[change]': analysis['top_terms'][0] if analysis['top_terms'] else 'change',
        '[document]': analysis['top_terms'][0] if analysis['top_terms'] else 'document',
        '[issue]': 'issue'  # Não temos como detectar automaticamente
    }
    
    for placeholder, replacement in placeholders.items():
        template = template.replace(placeholder, replacement)
    
    return template

def show_git_commands_menu():
    """Mostra menu de comandos Git adicionais"""
    while True:
        print("\n🔧 Comandos Git Adicionais:")
        print("1: git pull")
        print("2: git branch -a (listar todos branches)")
        print("3: git status")
        print("4: git log --oneline -5 (últimos 5 commits)")
        print("5: Outro comando personalizado")
        print("0: Voltar ao menu principal")
        
        choice = input("Escolha uma opção: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            run_git_command('git pull')
        elif choice == '2':
            run_git_command('git branch -a')
        elif choice == '3':
            run_git_command('git status')
        elif choice == '4':
            run_git_command('git log --oneline -5')
        elif choice == '5':
            custom_cmd = input("Digite o comando git completo: ").strip()
            if custom_cmd.startswith('git '):
                run_git_command(custom_cmd)
            else:
                print("❌ Por segurança, apenas comandos git são permitidos.")
        else:
            print("❌ Opção inválida")

def execute_smart_commit():
    """Executa o fluxo de commit inteligente"""
    counters = load_counters()
    analysis = analyze_changes()
    
    print("\n📜 Categorias de commit:")
    keys = list(commit_purposes.keys())
    for idx, key in enumerate(keys, 1):
        print(f"{idx}: {key.upper()}")
    
    category_choice = input("\nSelecione a categoria (ou 'c' para cancelar): ").strip()
    if category_choice.lower() == 'c':
        print("Operação cancelada.")
        return
    
    if not category_choice.isdigit() or not (1 <= int(category_choice) <= len(keys)):
        print("❌ Categoria inválida.")
        return
    
    category_key = keys[int(category_choice) - 1]
    variations = commit_purposes[category_key]
    
    print(f"\n✍️ Variações para {category_key.upper()}:")
    for idx, variation in enumerate(variations, 1):
        preview = replace_placeholders(variation, analysis)
        print(f"{idx}: {preview}")
    
    variation_choice = input("\nEscolha a variação (ou 'c' para cancelar): ").strip()
    if variation_choice.lower() == 'c':
        print("Operação cancelada.")
        return
    
    if not variation_choice.isdigit() or not (1 <= int(variation_choice) <= len(variations)):
        print("❌ Variação inválida.")
        return
    
    branch = confirm_branch(default_branch)
    if branch is None:
        return
    
    key_id = f"{category_key}-{variation_choice}"
    counters[key_id] = counters.get(key_id, 0) + 1
    
    base_message = variations[int(variation_choice) - 1]
    commit_message = replace_placeholders(base_message, analysis)
    commit_message = f"{commit_message} (-v{counters[key_id]})"
    
    print(f"\n📝 Commit message: {commit_message}")
    edit = input("Editar mensagem? (s/n): ").strip().lower()
    if edit == 's':
        commit_message = input("Digite a nova mensagem: ").strip()
    
    print(f"\n🔍 Alterações detectadas:")
    changed_files = analysis['changed_files']
    if changed_files:
        for file in changed_files[:5]:
            print(f"- {file}")
        if len(changed_files) > 5:
            print(f"- ... e mais {len(changed_files) - 5} arquivos")
    else:
        print("⚠️ Nenhuma alteração detectada.")
    
    if not has_changes():
        print("⚠️ Nenhuma alteração para commit.")
        return
    
    confirm = input("\nConfirmar commit e push? (s/n): ").strip().lower()
    if confirm != 's':
        print("Operação cancelada.")
        return
    
    run_git_command('git add .')
    run_git_command(f'git commit -m "{commit_message}"')
    
    result = run_git_command('git push')
    
    if 'has no upstream branch' in result.stderr:
        print(f"🔗 Branch '{branch}' não tem upstream. Configurando...")
        run_git_command(f'git push --set-upstream origin {branch}')
        print(f"✅ Upstream configurado: 'origin/{branch}'")
    elif result.returncode != 0:
        print(f"❌ Erro no push: {result.stderr}")
    else:
        print(f"✅ Push realizado com sucesso para '{branch}'!")
    
    save_counters(counters)

def main_menu():
    """Menu principal do sistema"""
    while True:
        print("\n🌿 Menu Principal Git:")
        print("1: Commit e Push Inteligente")
        print("2: Comandos Git Adicionais")
        print("0: Sair")
        
        choice = input("Escolha uma opção: ").strip()
        
        if choice == '0':
            print("Até logo! 👋")
            break
        elif choice == '1':
            execute_smart_commit()
        elif choice == '2':
            show_git_commands_menu()
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main_menu()