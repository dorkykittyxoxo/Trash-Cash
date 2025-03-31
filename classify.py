from flask import Flask, request, jsonify
import os
import logging
import traceback
from pymongo import MongoClient
from google.cloud import vision
from google.cloud.vision_v1 import types
from flask_cors import CORS  # Add CORS support for frontend requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Test the MongoDB connection first
try:
    client = MongoClient('mongodb+srv://Trash_Cash:1JQ1so8jcxrwfSlB@cluster0.omdanmm.mongodb.net/trashcash?retryWrites=true&w=majority', 
                         serverSelectionTimeoutMS=5000)
    # Force a connection to verify it works
    client.server_info()
    db = client['trashcash']
    waste_collection = db['waste_classification']
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    # We'll continue but flag that DB operations might fail

# Configure Google Vision API and test it
vision_client = None
try:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\Users\\91636\\Desktop\\Front-backend\\backend\\vision_api_key.json'
    vision_client = vision.ImageAnnotatorClient()
    logger.info("Google Vision client initialized")
except Exception as e:
    logger.error(f"Google Vision API configuration failed: {str(e)}")

# Predefined waste categories with expanded keywords for better matching
WASTE_CATEGORIES = {
    "plastic": {
        "points": 10, 
        "recycling": "Can be recycled at a plastic processing unit.",
        "keywords": ["plastic", "bottle", "container", "packaging", "polymer", "pet", "hdpe", "pvc", 
                    "ldpe", "pp", "polystyrene", "bag", "wrap", "trash bag", "straw", "cup"]
    },
    "paper": {
        "points": 5, 
        "recycling": "Recycle at a paper mill or use for compost.",
        "keywords": ["paper", "cardboard", "newspaper", "magazine", "book", "carton", "box", 
                    "tissue", "napkin", "document", "receipt", "envelope", "mail"]
    },
    "metal": {
        "points": 20, 
        "recycling": "Recycle at a metal scrapyard.",
        "keywords": ["metal", "aluminum", "tin", "steel", "iron", "copper", "bronze", "can", 
                    "foil", "scrap metal", "wire", "nail", "silverware", "utensil"]
    },
    "glass": {
        "points": 15, 
        "recycling": "Recycle at a glass processing unit.",
        "keywords": ["glass", "bottle", "jar", "window", "mirror", "glassware", "cup", 
                    "drinking glass", "wine glass", "beer bottle", "vase"]
    },
    "organic": {
        "points": 2, 
        "recycling": "Use for composting or biogas generation.",
        "keywords": ["food", "vegetable", "fruit", "leaf", "plant", "garden waste", "compost", 
                    "biodegradable", "organic", "wood", "grass", "flower", "peel", "coffee", "tea"]
    }
}

@app.route('/test-vision', methods=['POST'])
def test_vision_api():
    """Test endpoint for Vision API only"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        image_file = request.files['image']
        image_bytes = image_file.read()
        
        if not vision_client:
            return jsonify({"error": "Vision API client not initialized"}), 500
            
        image = types.Image(content=image_bytes)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations
        
        return jsonify({
            "status": "success",
            "labels": [{"description": label.description, "score": label.score} for label in labels]
        })
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Vision API test failed: {error_details}")
        return jsonify({"error": str(e), "traceback": error_details}), 500

@app.route('/test-db', methods=['GET'])
def test_database():
    """Test endpoint for database connection"""
    try:
        # Try to insert and retrieve a test document
        test_id = waste_collection.insert_one({"test": "connection"}).inserted_id
        result = waste_collection.find_one({"_id": test_id})
        waste_collection.delete_one({"_id": test_id})
        
        return jsonify({
            "status": "success",
            "message": "Database connection and operations working"
        })
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Database test failed: {error_details}")
        return jsonify({"error": str(e), "traceback": error_details}), 500

@app.route('/classify', methods=['POST'])
def classify_waste():
    try:
        logger.info("Received classification request")
        
        # Check if image is in request
        if 'image' not in request.files:
            logger.error("No image file in request")
            return jsonify({"error": "No image file provided"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            logger.error("Empty filename")
            return jsonify({"error": "Empty filename"}), 400
            
        logger.info(f"Processing image: {image_file.filename}")
        
        # Read the image
        image_bytes = image_file.read()
        
        # Check if vision client is initialized
        if not vision_client:
            logger.error("Vision API client not initialized")
            return jsonify({"error": "Vision API client not initialized"}), 500
            
        # Send to Vision API
        image = types.Image(content=image_bytes)
        response = vision_client.label_detection(image=image)
        labels = response.label_annotations
        
        # Log detected labels
        logger.info(f"Detected labels: {[label.description for label in labels]}")
        
        if not labels:
            logger.warning("No labels detected by Vision API")
            return jsonify({
                "category": "unknown", 
                "points": 0, 
                "recycling_info": "No objects detected in image. Please try a clearer image.",
                "detected_labels": []
            })
        
        # Determine waste category based on detected labels
        detected_labels = [label.description.lower() for label in labels]
        
        # Find the category with the most keyword matches
        best_category = "unknown"
        max_matches = 0
        
        for category, info in WASTE_CATEGORIES.items():
            # Check for keyword matches in labels
            matches = 0
            for label in detected_labels:
                for keyword in info["keywords"]:
                    if keyword in label:
                        matches += 1
                    if keyword == label:
                        matches += 2  # Extra weight for exact matches
            
            logger.debug(f"Category {category} matches: {matches}")
            
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        # Assign points and recycling guidelines
        if best_category in WASTE_CATEGORIES and max_matches > 0:
            assigned_category = best_category
            points = WASTE_CATEGORIES[assigned_category]['points']
            recycling_info = WASTE_CATEGORIES[assigned_category]['recycling']
        else:
            assigned_category = "unknown"
            points = 0
            recycling_info = "Waste category not recognized. Please dispose responsibly."
        
        logger.info(f"Classified as {assigned_category} with {max_matches} matches")
        
        # Try to store in MongoDB
        try:
            waste_data = {
                "image_name": image_file.filename,
                "category": assigned_category,
                "points": points,
                "recycling_info": recycling_info,
                "detected_labels": [label.description for label in labels]
            }
            waste_collection.insert_one(waste_data)
            logger.info("Successfully saved to database")
        except Exception as db_error:
            logger.error(f"Database operation failed: {str(db_error)}")
            # Continue even if DB fails - still return the classification
        
        return jsonify({
            "category": assigned_category, 
            "points": points, 
            "recycling_info": recycling_info,
            "confidence": max_matches if max_matches > 0 else 0,
            "detected_labels": [label.description for label in labels]
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Classification failed: {error_details}")
        return jsonify({"error": str(e), "traceback": error_details}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API is running"})

if __name__ == '__main__':
    logger.info("Starting waste classification API server")
    app.run(debug=True, host='0.0.0.0', port=5000)