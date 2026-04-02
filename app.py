from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import requests
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms
from dotenv import load_dotenv
from googletrans import Translator
import cv2
import re
import datetime

# ===============================
# ENV CONFIG
# ===============================
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

translator = Translator()

CURRENT_YEAR = datetime.datetime.now().year

# ===============================
# FAKE NEWS DETECTION (Advanced Logic)
# ===============================
def detect_fake_news(query):

    enhanced_query = query + " latest news article"

    CREDIBLE_DOMAINS = [
        'bbc.com', 'cnn.com', 'reuters.com',
        'nytimes.com', 'theguardian.com',
        'indiatoday.in', 'ndtv.com',
        'thehindu.com', 'hindustantimes.com',
        'timesofindia.indiatimes.com',
        '.gov', '.edu'
    ]

    FAKE_DOMAINS = [
        'theonion.com', 'infowars.com',
        'clickhole.com', 'babylonbee.com'
    ]

    SUSPICIOUS_KEYWORDS = [
        'shocking', 'miracle', 'conspiracy',
        'aliens', 'secret', 'hoax',
        'viral', 'banned', 'exposed',
        'cure all', '100% guaranteed',
        'government hiding', 'proof finally revealed'
    ]

    fake_score = 0
    real_score = 0
    links = []

    # ===============================
    # GOOGLE SOURCE CHECK
    # ===============================
    try:
        search_url = (
            f"https://www.googleapis.com/customsearch/v1?q={enhanced_query}"
            f"&key={API_KEY}"
            f"&cx={CX}"
        )

        response = requests.get(search_url, timeout=5)
        data = response.json()
        items = data.get("items", [])

        for item in items[:5]:
            title = item.get("title", "No Title")
            link = item.get("link", "")
            links.append((title, link))

            if any(domain in link for domain in CREDIBLE_DOMAINS):
                real_score += 2

            if any(domain in link for domain in FAKE_DOMAINS):
                fake_score += 3

    except Exception:
        pass  # Continue with fallback logic

    # ===============================
    # SUSPICIOUS KEYWORD CHECK
    # ===============================
    for word in SUSPICIOUS_KEYWORDS:
        if word.lower() in query.lower():
            fake_score += 2

    # ===============================
    # FUTURE YEAR DETECTION
    # ===============================
    years = re.findall(r'\b(20\d{2})\b', query)
    for year in years:
        if int(year) > CURRENT_YEAR:
            fake_score += 2

    # ===============================
    # UNREALISTIC CLAIM PATTERNS
    # ===============================
    unrealistic_patterns = [
        "earth will go dark",
        "aliens landed",
        "government replaced",
        "cures all diseases",
        "won fifa world cup"
    ]

    for pattern in unrealistic_patterns:
        if pattern.lower() in query.lower():
            fake_score += 3

    # ===============================
    # ABSOLUTE CLAIM DETECTION
    # ===============================
    if re.search(r'\b(always|never|100%|guaranteed|everyone)\b', query.lower()):
        fake_score += 1

    # ===============================
    # FINAL DECISION
    # ===============================
    if fake_score > real_score:
        return "Fake", links, 30
    else:
        return "Real", links, 75


# ===============================
# CNN MODEL FOR IMAGE & VIDEO
# ===============================
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 64 * 64, 128),
            nn.ReLU(),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


morph_model = SimpleCNN()
morph_model.load_state_dict(
    torch.load('morph_model.pth', map_location=torch.device('cpu'))
)
morph_model.eval()


# ===============================
# IMAGE DETECTION
# ===============================
def detect_image_morphing(image_path):
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])

    img = Image.open(image_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = morph_model(img_tensor)
        probs = torch.softmax(output, dim=1)
        pred = torch.argmax(probs).item()
        confidence = round(float(probs[0][pred]) * 100, 2)

        label = "Morphed" if pred == 0 else "Original"
        return label, confidence


# ===============================
# VIDEO DETECTION
# ===============================
def detect_video_deepfake(video_path):
    cap = cv2.VideoCapture(video_path)

    frame_count = 0
    morphed_count = 0
    total_confidence = 0

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 40 == 0:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tensor = transform(img).unsqueeze(0)

            with torch.no_grad():
                output = morph_model(img_tensor)
                probs = torch.softmax(output, dim=1)
                pred = torch.argmax(probs).item()
                confidence = float(probs[0][pred]) * 100

                total_confidence += confidence
                if pred == 0:
                    morphed_count += 1

        frame_count += 1

    cap.release()

    if frame_count == 0:
        return "Invalid Video", 0

    avg_confidence = round(total_confidence / max(1, frame_count//20), 2)

    if morphed_count > (frame_count//40):
        return "Deepfake Detected", avg_confidence
    else:
        return "Authentic Video", avg_confidence


# ===============================
# ROUTES
# ===============================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    user_input = request.form.get("user_input", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    detected = translator.detect(user_input)
    source_lang = detected.lang

    translated = translator.translate(user_input, dest="en")
    translated_text = translated.text

    result, links, accuracy = detect_fake_news(translated_text)

    final_result = translator.translate(result, dest=source_lang).text

    return jsonify({
        "prediction": final_result,
        "accuracy": accuracy,
        "links": links,
        "language": source_lang
    })


@app.route("/predict_image", methods=["POST"])
def predict_image():
    file = request.files["image_file"]
    filename = secure_filename(file.filename)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    result, accuracy = detect_image_morphing(filepath)

    return jsonify({
        "prediction": result,
        "accuracy": accuracy
    })


@app.route("/predict_video", methods=["POST"])
def predict_video():
    file = request.files["video_file"]
    filename = secure_filename(file.filename)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    result, accuracy = detect_video_deepfake(filepath)

    return jsonify({
        "prediction": result,
        "accuracy": accuracy
    })


if __name__ == "__main__":
    app.run(debug=True)