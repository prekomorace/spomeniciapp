from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from ultralytics import YOLO
import os
import torch

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploadovane_slike'
# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MODEL_PATH = 'spomenici.pt'  # Path to your YOLOv8 model weights

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max file size 16MB

# Check if CUDA is available, otherwise use CPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Load YOLOv8 model (load once and reuse)
model = YOLO(MODEL_PATH)
model.to(device)  # Will use CPU if CUDA not available


def allowed_file(filename):
    """Check if the uploaded file is of allowed type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_file():
    """Render the file upload form."""
    return render_template('index.html')


@app.route('/uploader', methods=['POST'])
def upload_image():
    """Handle image upload and processing."""
    if 'file' not in request.files:
        return redirect(url_for('upload_file'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('upload_file'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  # Save the uploaded file

        # Run the YOLO model for inference
        results = model(filepath)
        for r in results:
            if len(r.boxes.cls) > 0:  # Check if r.boxes.cls is not empty
                class_id = r.boxes.cls[0]  # Access the first class_id of the detection
                label = r.names[int(class_id)]  # Get the label from YOLO's class names

                # Plot the detection results
                im_array = r.plot()  
                im = Image.fromarray(im_array[..., ::-1])  # Convert to RGB
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
                im.save(output_path)  # Save the processed image

                # Return the result page with the processed image and label
                return render_template('results.html', filename='uploadovane_slike/processed_' + filename, label=label)
            else:
                return render_template('error.html', message="No objects detected.")
        return render_template('error.html', message="An error occurred during processing.")

    return redirect(url_for('upload_file'))  # Redirect if file is not valid


# For Render and other PaaS, use gunicorn to serve the app
if __name__ == "__main__":
    # Use this for local development
    app.run(debug=True)
    # When deployed, gunicorn will serve the app