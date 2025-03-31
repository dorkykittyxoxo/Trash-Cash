from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from classify import classify_waste  # Import Google Vision API function

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Waste-to-EcoCoins mapping
ECOCOIN_VALUES = {
    "Plastic": 10,
    "Paper": 5,
    "Metal": 15,
    "Glass": 8,
    "Organic": 3,
    "E-Waste": 20,
    "Other": 2
}

# Recycling tips
RECYCLING_GUIDELINES = {
    "Plastic": "Rinse and recycle plastic bottles. Avoid single-use plastics.",
    "Paper": "Recycle newspapers, magazines, and cardboard. Avoid greasy paper.",
    "Metal": "Recycle aluminum cans and steel items. Rinse before recycling.",
    "Glass": "Recycle glass bottles and jars. Avoid broken glass.",
    "Organic": "Compost food scraps and garden waste.",
    "E-Waste": "Drop off at an authorized e-waste recycling center.",
    "Other": "Dispose of responsibly. Check local recycling rules."
}

@app.route("/")
def home():
    return "TrashCash AI Backend Running!"

@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # Classify waste using Google Vision API
   
    waste_category = classify_waste(filepath)
    eco_coins = ECOCOIN_VALUES.get(waste_category, 0)
    recycling_tip = RECYCLING_GUIDELINES.get(waste_category, "No guidelines available.")

    return jsonify({
        "waste_type": waste_category,
        "eco_coins": eco_coins,
        "recycling_tip": recycling_tip
    })

if __name__ == "__main__":
    app.run(debug=True)
