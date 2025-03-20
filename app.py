from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from ultralytics import YOLO
import os
import torch

app = Flask(__name__)

# Konfiguracija
UPLOAD_FOLDER = 'static/uploadovane_slike'
# Osiguraj da folder postoji
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MODEL_PATH = 'spomenici.pt'  # Putanja do vaših YOLOv8 model weight-a

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maksimalna veličina fajla 16MB

# Ruta za posluživanje service-worker.js s root scope-a
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'service-worker.js')

# Provjera da li CUDA postoji, inače koristi CPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Učitaj YOLOv8 model (učitava se jednom i ponovo se koristi)
model = YOLO(MODEL_PATH)
model.to(device)  # Koristit će CPU ako CUDA nije dostupna

def allowed_file(filename):
    """Provjeri je li uploadani fajl dozvoljenog tipa."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_file():
    """Prikazuje formu za upload."""
    return render_template('index.html')

@app.route('/uploader', methods=['POST'])
def upload_image():
    """Rukuje uploadom i obradom slike."""
    if 'file' not in request.files:
        return redirect(url_for('upload_file'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('upload_file'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  # Spremi uploadanu sliku

        # Pokreni YOLO model za inferencu
        results = model(filepath)
        for r in results:
            if len(r.boxes.cls) > 0:  # Provjeri postoji li detekcija
                class_id = r.boxes.cls[0]  # Uzmi prvu detekciju
                label = r.names[int(class_id)]  # Preuzmi labelu iz YOLO modela

                # Prikaz rezultata
                im_array = r.plot()
                im = Image.fromarray(im_array[..., ::-1])  # Pretvori u RGB
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
                im.save(output_path)  # Spremi obrađenu sliku

                # Prikazi stranicu s rezultatom
                return render_template('results.html', filename='uploadovane_slike/processed_' + filename, label=label)
            else:
                return render_template('error.html', message="Nije pronađen nijedan objekt.")
        return render_template('error.html', message="Došlo je do greške prilikom obrade.")
    return redirect(url_for('upload_file'))

if __name__ == "__main__":
    # Za lokalni razvoj
    app.run(debug=True)
    # U produkciji se koristi gunicorn ili neki drugi WSGI server
