"""
MarkItDown - Interfaz web local para convertir archivos a Markdown.
Ejecutar: python app.py
Abrir: http://localhost:5000
"""

import os
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string
from markitdown import MarkItDown

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

md = MarkItDown()

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MarkItDown</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #1a1a1a; min-height: 100vh; }
  header { background: #1a1a1a; color: #fff; padding: 1rem 2rem; display: flex; align-items: center; gap: 0.75rem; }
  header h1 { font-size: 1.2rem; font-weight: 500; }
  header span { font-size: 0.85rem; color: #888; }
  main { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }
  #dropzone {
    border: 2px dashed #ccc; border-radius: 12px; background: #fff;
    padding: 3rem 2rem; text-align: center; cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
  }
  #dropzone.dragover { border-color: #2563eb; background: #eff6ff; }
  #dropzone p { color: #555; margin-top: 0.5rem; font-size: 0.95rem; }
  #dropzone strong { font-size: 1.1rem; color: #1a1a1a; }
  #dropzone input[type=file] { display: none; }
  .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
  #file-list { margin-top: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
  .file-card {
    background: #fff; border-radius: 10px; padding: 1rem 1.25rem;
    border: 1px solid #e5e5e5; display: flex; flex-direction: column; gap: 0.5rem;
  }
  .file-header { display: flex; justify-content: space-between; align-items: center; }
  .file-name { font-weight: 500; font-size: 0.95rem; word-break: break-all; }
  .badge {
    font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 99px;
    background: #e5e7eb; color: #374151; white-space: nowrap;
  }
  .badge.ok { background: #d1fae5; color: #065f46; }
  .badge.err { background: #fee2e2; color: #991b1b; }
  .badge.loading { background: #dbeafe; color: #1e40af; }
  .preview {
    background: #f9fafb; border-radius: 6px; padding: 0.75rem 1rem;
    font-family: monospace; font-size: 0.82rem; white-space: pre-wrap;
    max-height: 200px; overflow-y: auto; color: #374151;
    border: 1px solid #e5e5e5; display: none;
  }
  .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  button {
    padding: 0.4rem 0.9rem; border-radius: 6px; border: 1px solid #d1d5db;
    background: #fff; color: #374151; cursor: pointer; font-size: 0.85rem;
    transition: background 0.15s;
  }
  button:hover { background: #f3f4f6; }
  button.primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
  button.primary:hover { background: #333; }
  #clear-btn { margin-top: 1rem; }
  .error-msg { color: #991b1b; font-size: 0.85rem; }
</style>
</head>
<body>
<header>
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/>
    <line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
  <h1>MarkItDown</h1>
  <span>Convierte archivos a Markdown</span>
</header>
<main>
  <div id="dropzone" onclick="document.getElementById('file-input').click()">
    <div class="icon">📂</div>
    <strong>Arrastra archivos aquí</strong>
    <p>o haz clic para seleccionar</p>
    <p style="margin-top:0.75rem; font-size:0.8rem; color:#999">
      PDF · DOCX · XLSX · PPTX · HTML · CSV · imágenes · audio · ZIP · y más
    </p>
    <input type="file" id="file-input" multiple>
  </div>
  <div id="file-list"></div>
  <button id="clear-btn" style="display:none" onclick="clearAll()">Limpiar todo</button>
</main>

<script>
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const clearBtn = document.getElementById('clear-btn');

dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  handleFiles([...e.dataTransfer.files]);
});
fileInput.addEventListener('change', () => handleFiles([...fileInput.files]));

function handleFiles(files) {
  files.forEach(processFile);
  clearBtn.style.display = 'inline-block';
}

function processFile(file) {
  const card = document.createElement('div');
  card.className = 'file-card';
  card.innerHTML = `
    <div class="file-header">
      <span class="file-name">${file.name}</span>
      <span class="badge loading">Convirtiendo...</span>
    </div>
    <div class="preview"></div>
    <div class="actions"></div>
  `;
  fileList.prepend(card);

  const badge = card.querySelector('.badge');
  const preview = card.querySelector('.preview');
  const actions = card.querySelector('.actions');

  const formData = new FormData();
  formData.append('file', file);

  fetch('/convert', { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        badge.className = 'badge err';
        badge.textContent = 'Error';
        const msg = document.createElement('div');
        msg.className = 'error-msg';
        msg.textContent = data.error;
        card.insertBefore(msg, actions);
        return;
      }
      badge.className = 'badge ok';
      badge.textContent = 'Listo';
      preview.style.display = 'block';
      preview.textContent = data.preview;

      const btnPreview = document.createElement('button');
      btnPreview.textContent = 'Ver más';
      btnPreview.onclick = () => {
        if (preview.style.maxHeight === 'none') {
          preview.style.maxHeight = '200px';
          btnPreview.textContent = 'Ver más';
        } else {
          preview.style.maxHeight = 'none';
          btnPreview.textContent = 'Ver menos';
        }
      };

      const btnCopy = document.createElement('button');
      btnCopy.textContent = 'Copiar';
      btnCopy.onclick = () => {
        navigator.clipboard.writeText(data.text).then(() => {
          btnCopy.textContent = 'Copiado!';
          setTimeout(() => btnCopy.textContent = 'Copiar', 1500);
        });
      };

      const btnDl = document.createElement('button');
      btnDl.className = 'primary';
      btnDl.textContent = 'Descargar .md';
      btnDl.onclick = () => {
        const blob = new Blob([data.text], { type: 'text/markdown' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = file.name.replace(/\.[^.]+$/, '') + '.md';
        a.click();
      };

      actions.append(btnPreview, btnCopy, btnDl);
    })
    .catch(() => {
      badge.className = 'badge err';
      badge.textContent = 'Error de red';
    });
}

function clearAll() {
  fileList.innerHTML = '';
  clearBtn.style.display = 'none';
  fileInput.value = '';
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "No se recibió ningún archivo"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    suffix = Path(file.filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = md.convert(tmp_path)
        text = result.text_content or ""
        preview = text[:2000] + ("..." if len(text) > 2000 else "")
        return jsonify({"text": text, "preview": preview})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    import threading
    import webbrowser
    def abrir():
        import time
        time.sleep(1.2)
        webbrowser.open("http://localhost:5000")
    threading.Thread(target=abrir, daemon=True).start()
    print("MarkItDown corriendo en http://localhost:5000")
    app.run(debug=False, port=5000)
