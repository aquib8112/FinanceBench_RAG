import modal
import os

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install_from_requirements("backend/requirements.txt")
    .add_local_dir(
        "backend", 
        remote_path="/root/backend", 
        copy=True,
        ignore=[".env.py", "__pycache__", ".venv", ".pytest_cache"]
    )
    .run_commands("cd /root/backend && python -m rag.download_model")
)

app = modal.App("financebench-backend")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("my-google-ai-secret")],
    cpu=2.0,
    memory=4096, 
    timeout=600,
)
@modal.asgi_app()
def api():
    import sys
    import os
    
    backend_path = "/root/backend"
    os.chdir(backend_path)
    
    if backend_path not in sys.path:
        sys.path.append(backend_path)
    
    from server import app as local_fastapi_app
    return local_fastapi_app