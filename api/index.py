import os
import logging
import json
from typing import Tuple, Any

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Configuration Loading ---

# Check for demo/mock mode
mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

# API Key (Essential, unless in mock mode)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key and not mock_mode:
    logging.critical("GOOGLE_API_KEY not found in environment variables. Application cannot start without MOCK_MODE=true.")
    # In a real app, might exit or raise a specific ConfigError
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file or enable MOCK_MODE=true.")

# Gemini Model Config (with defaults)
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro-exp-03-25")
temperature = float(os.getenv("GEMINI_TEMPERATURE", 0.2))
max_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", 2048))

# Flask Config (with defaults)
port = int(os.getenv("PORT", 5000))
host = os.getenv("HOST", "0.0.0.0")
debug_mode = os.getenv("FLASK_ENV", "development") == "development"
# Set max content length (e.g., 16MB) for larger image uploads
MAX_CONTENT_MB = 16

# --- Logging Setup ---
log_level = logging.DEBUG if debug_mode else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")
logger.info(f"Flask ENV: {os.getenv('FLASK_ENV', 'development')}")
logger.info(f"Debug mode: {debug_mode}")
logger.info(f"Mock mode: {mock_mode}")
logger.info(f"Max content length: {MAX_CONTENT_MB} MB")
if not mock_mode:
    logger.info(f"Using Gemini Model: {model_name}")
else:
    logger.warning("Running in MOCK MODE - No actual Gemini API calls will be made")

# --- Flask Application Setup ---

# Initialize Flask app
app = Flask(__name__)
# Configure max content length
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_MB * 1024 * 1024

# Enable CORS for the frontend
CORS(app)

# Initialize Gemini model if not in mock mode
if not mock_mode:
    try:
        # Import here to potentially avoid issues if gemini client fails
        from .gemini_client import initialize_gemini
        initialize_gemini(api_key=api_key, model_name=model_name)
    except ImportError:
        logger.critical("CRITICAL: Could not import gemini_client.py. Ensure the file exists and has no syntax errors.", exc_info=True)
    except Exception as e:
        # Log critical error if model initialization fails
        logger.critical(f"CRITICAL: Failed to initialize Gemini model: {str(e)}", exc_info=True)
        # The application might still run, but the /api/solve endpoint will fail.
else:
    # Mock response function used in MOCK_MODE
    def generate_mock_response(problem_text=None, image_data_base64=None, **kwargs):
        """Generate a mock response for testing without Gemini API."""
        logger.info("Generating mock response")
        
        # For empty/invalid input
        if not problem_text and not image_data_base64:
            return {"error": "No input provided", "details": "Please provide either text or image input"}
            
        # Mock error cases for testing
        if problem_text and "error" in problem_text.lower():
            return {"error": "Mock Error", "details": "This is a simulated error response for testing"}
            
        # Generate appropriate mock response based on input
        # For quadratic or basic math problems
        if problem_text and any(term in problem_text.lower() for term in ["solve", "equation", "x", "quadratic"]):
            return {
                "solution": "Step 1: Identify the coefficients in the standard form ax² + bx + c = 0\nStep 2: Use the quadratic formula x = (-b ± √(b² - 4ac)) / 2a\nStep 3: Calculate the discriminant b² - 4ac\nStep 4: Find the solutions x₁ = (-b + √(b² - 4ac)) / 2a and x₂ = (-b - √(b² - 4ac)) / 2a",
                "explanation": "The quadratic formula allows us to find the solutions to any quadratic equation. The discriminant (b² - 4ac) tells us how many solutions exist: if positive, there are two real solutions; if zero, there's one real solution; if negative, there are two complex solutions.",
                "practice_questions": [
                    "Solve for x: 3x² - 6x + 2 = 0",
                    "Solve for x: x² + 4x - 12 = 0"
                ]
            }
        # For physics problems
        elif problem_text and any(term in problem_text.lower() for term in ["force", "velocity", "physics", "newton"]):
            return {
                "solution": "Step 1: Identify the given quantities and variables\nStep 2: Determine the relevant physics formula\nStep 3: Substitute the known values into the formula\nStep 4: Solve for the unknown variable\nStep 5: Check units and ensure the answer makes physical sense",
                "explanation": "This problem involves Newton's laws of motion, which describe the relationship between an object and the forces acting upon it. The second law (F = ma) states that force equals mass times acceleration.",
                "practice_questions": [
                    "A 2kg object experiences a net force of 10N. What is its acceleration?",
                    "How much force is needed to accelerate a 1500kg car from 0 to 27 m/s in 10 seconds?"
                ]
            }
        # For chemistry problems
        elif problem_text and any(term in problem_text.lower() for term in ["chemistry", "molecule", "reaction", "acid"]):
            return {
                "solution": "Step 1: Balance the chemical equation\nStep 2: Identify reactants and products\nStep 3: Calculate molar masses\nStep 4: Apply stoichiometric principles\nStep 5: Calculate the final answer",
                "explanation": "Chemical reactions follow the law of conservation of mass, meaning the total mass of the elements before and after the reaction must be the same. This is why we balance chemical equations.",
                "practice_questions": [
                    "Balance the following equation: H₂ + O₂ → H₂O",
                    "How many grams of water can be produced from 4 grams of hydrogen gas reacting with excess oxygen?"
                ]
            }
        # For image inputs
        elif image_data_base64:
            return {
                "solution": "Step 1: Analyze the problem presented in the image\nStep 2: Apply the appropriate formula or theorem\nStep 3: Solve step-by-step following mathematical rules\nStep 4: Double-check the solution",
                "explanation": "This problem can be solved using algebraic manipulation. We isolate the variable by performing the same operation on both sides of the equation, maintaining equality throughout the process.",
                "practice_questions": [
                    "Try solving a similar problem with different values",
                    "Solve the problem using an alternative method"
                ]
            }
        # Default response
        else:
            return {
                "solution": "Here's a step-by-step solution to your problem:\n1. First, understand what the problem is asking\n2. Identify the key information and variables\n3. Select the appropriate formula or approach\n4. Solve methodically, showing each step\n5. Verify the answer makes sense",
                "explanation": "This type of problem requires a systematic approach. By breaking it down into manageable steps, we can solve it efficiently.",
                "practice_questions": [
                    "Here's a similar problem to try: Can you solve a variation of this problem where the values are slightly different?",
                    "Try this challenge problem that uses the same concept but in a different context."
                ]
            }

# --- API Endpoints ---

@app.route('/api/solve', methods=['POST'])
def handle_solve() -> Tuple[Response, int]:
    """
    API endpoint to solve STEM problems using Gemini.
    
    Expects JSON input with either 'text_problem', 'image_data', or both.
    Returns JSON response with solution, explanation, and practice questions.
    """
    # Check content type before accessing request data which might trigger MAX_CONTENT_LENGTH error
    if not request.is_json:
        content_type = request.headers.get('Content-Type', 'N/A')
        logger.warning(f"Received non-JSON request for /api/solve. Content-Type: {content_type}")
        return jsonify({"error": "Request must be JSON"}), 400
    
    # Get JSON data - this might fail if MAX_CONTENT_LENGTH is exceeded
    try:
        data = request.get_json()
    except Exception as e:
        # Check if the error is related to content length
        if 'Request Entity Too Large' in str(e):
             logger.warning(f"Request entity too large (Limit: {MAX_CONTENT_MB}MB). Error: {str(e)}")
             return jsonify({"error": "Request failed", "details": f"Input data too large. Maximum size is {MAX_CONTENT_MB}MB."}), 413 # Payload Too Large status code
        logger.error(f"Error getting JSON data from request: {str(e)}", exc_info=True)
        return jsonify({"error": "Invalid JSON data received"}), 400

    if not data:
        logger.warning("/api/solve received empty JSON data")
        return jsonify({"error": "Request body cannot be empty JSON"}), 400
    
    # Extract inputs
    text_problem = data.get('text_problem')
    image_data = data.get('image_data') # Base64 string from frontend
    
    # Validate input
    if not text_problem and not image_data:
        logger.warning("/api/solve called with no text_problem or image_data")
        return jsonify({"error": "No input provided", "details": "Please provide either text or image input"}), 400
    
    text_provided = "yes" if text_problem else "no"
    image_provided = "yes" if image_data else "no"
    # Log size of image data if present
    image_size_info = f", Image Size (approx Base64 KiB): {len(image_data) * 3 / 4 / 1024:.2f}" if image_data else ""
    logger.info(f"Received request for /api/solve (Text: {text_provided}, Image: {image_provided}{image_size_info})")

    try:
        # Call appropriate service based on mode
        if mock_mode:
            logger.debug("Calling generate_mock_response")
            result = generate_mock_response(
                problem_text=text_problem,
                image_data_base64=image_data
            )
        else:
            # Import here only if needed and not in mock mode
            try:
                from .gemini_client import generate_stem_response
                logger.debug("Calling generate_stem_response")
                result = generate_stem_response(
                    problem_text=text_problem,
                    image_data_base64=image_data,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except ImportError:
                logger.error("Failed to import generate_stem_response from gemini_client.", exc_info=True)
                return jsonify({"error": "Could not load Gemini client."}), 500 # Send error to frontend
            except Exception as e: # Catch errors during generation
                logger.error(f"Error in generate_stem_response: {str(e)}", exc_info=True)
                return jsonify({"error": "An internal server error occurred", "details": "An unexpected error occurred while processing the request."}), 500
        
        # Check for errors returned from the client function
        if result and isinstance(result, dict) and "error" in result:
            error_source = 'mock response' if mock_mode else 'gemini_client'
            logger.error(f"Error from {error_source}: {result.get('error')} - {result.get('details')}")
            # Return 500 for internal errors (API, parsing, model init issues)
            # Use 400 for specific input errors like invalid image data
            if result.get("error") == "Invalid image data":
                 return jsonify(result), 400
            return jsonify(result), 500
        
        # Return successful response
        logger.info("Successfully generated response for /api/solve")
        return jsonify(result), 200
    
    except Exception as e:
        # Handle unexpected errors during the process
        logger.error(f"Unexpected error in /api/solve handler: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred", "details": "An unexpected error occurred while processing the request."}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """Simple health check endpoint to verify the server is running."""
    logger.debug("Health check endpoint called")
    return jsonify({"status": "ok", "message": "STEM Helper API is running"}), 200

# Run the app
if __name__ == '__main__':
    logger.info(f"Starting server on {host}:{port} with debug={debug_mode}")
    app.run(debug=debug_mode, host=host, port=port) 
