# 🐙 GCA — Git Commit Assistant

Uma CLI simples para facilitar e agilizar commits no Git com mensagens padronizadas, interativas ou customizadas.

Não me julgue sem ler : https://automatetheboringstuff.com/..-- 

Vídeo rápido rodando - https://i.imgur.com/IBKchDS.mp4

---

## 🚀 Instalação

### Pré-requisitos

* Python ≥ 3.10
* Git configurado com SSH
* Sistema: Arch Linux / EndeavourOS (ou compatível)

### Passos

#### Python

1️⃣ Salve o script [gca.py](https://raw.github.com/NonakaVal/lazy-commits/main/gca.py):

```bash
nano ~/gca.py
```

Cole o código do script e adicione no topo:

```python
#!/usr/bin/env python3
```

Depois:

```bash
chmod +x ~/gca.py
```

2️⃣ Torne o comando global:

```bash
mkdir -p ~/.local/bin
ln -s ~/gca.py ~/.local/bin/gca
```

3️⃣ Garanta que `~/.local/bin` está no seu PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

#### bash (arch linux)
---

1. Salve o [arquivo](https://raw.github.com/NonakaVal/lazy-commits/main/gca) como `gca`:

```bash
sudo nano /usr/local/bin/gca
```

2. Cole o script acima.

3. Salvar → CTRL+O → ENTER → CTRL+X

4. Dê permissão de execução:

```bash
sudo chmod +x /usr/local/bin/gca
```

5. Agora, você pode rodar:

```bash
gca
```

Dentro de qualquer repositório git.


## 🧪 Uso - 

### Executar

No diretório de um repositório Git, rode:

```bash
gca
```

### Funcionalidades

* Commit guiado com mensagens padrão
* Commit customizado com detecção automática do tipo
* Confirmação antes do commit e do push
* Compatível com Git via SSH
* Sempre atua na pasta atual

---

## 📋 Licença

MIT — veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---




