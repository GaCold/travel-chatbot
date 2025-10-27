#### Install Ollama Local

```bash
curl -fsSL https://ollama.com/install.sh | sh
```
##### Pull model
```bash
ollama run qwen2:7b
```

#### config package
```bash
pip install -r server/requirements.txt
```

#### start app
```bash
source .venv/bin/activate
python3 server/main.py
```