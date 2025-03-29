import os
import json
import base64
import io
import logging
from typing import Dict, Any, Optional, Union

from PIL import Image
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Get logger instance
logger = logging.getLogger(__name__)

# Global model instance
model: Optional[genai.GenerativeModel] = None

def initialize_gemini(api_key: str, model_name: str) -> None:
    """
    Initialize the Gemini model with the provided API key and model name.
    
    Args:
        api_key (str): The Google API key for Gemini access
        model_name (str): The name of the Gemini model to use
        
    Raises:
        Exception: If model initialization fails
    """
    try:
        genai.configure(api_key=api_key)
        global model
        model = genai.GenerativeModel(model_name)
        # Test if model is accessible by generating a small test content
        _ = model.generate_content("Test initialization")
        logger.info(f"Gemini model '{model_name}' initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Gemini model '{model_name}': {str(e)}")
        # Reraise the exception to be handled by the caller (app.py)
        raise Exception(f"Failed to initialize Gemini model '{model_name}': {str(e)}")

def generate_stem_response(
    problem_text: Optional[str] = None, 
    image_data_base64: Optional[str] = None,
    temperature: float = 1,
    max_tokens: int = 65536
) -> Dict[str, Any]:
    """
    Generate a STEM problem solution using the Gemini model.
    
    Args:
        problem_text (str, optional): Text description of the STEM problem
        image_data_base64 (str, optional): Base64-encoded image of the STEM problem
        temperature (float): Sampling temperature for generation
        max_tokens (int): Maximum number of tokens to generate
        
    Returns:
        dict: JSON response containing solution, explanation, and practice questions, 
              or an error dictionary.
    """
    # Input validation
    if not model:
        logger.error("generate_stem_response called before model initialization.")
        return {"error": "Model not initialized", "details": "Gemini model is not available"}
    
    if not problem_text and not image_data_base64:
        logger.warning("generate_stem_response called with no input.")
        return {"error": "No input provided", "details": "Please provide either text or image input"}
    
    # Prepare prompt parts
    prompt_parts: list[Union[str, Dict]] = []
    image_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None
    
    # Process image if provided
    if image_data_base64:
        logger.debug("Processing image data...")
        try:
            # Remove potential prefix in base64 string
            logger.debug("Checking for Base64 prefix...")
            if "," in image_data_base64:
                image_data_base64 = image_data_base64.split(",", 1)[1]
                logger.debug("Base64 prefix removed.")

            # Decode base64 to bytes
            logger.debug("Decoding Base64 string to bytes...")
            image_bytes = base64.b64decode(image_data_base64)
            logger.debug(f"Decoded image to {len(image_bytes)} bytes.")

            # Use PIL to open the image from bytes to determine format
            logger.debug("Opening image with Pillow to determine format...")
            img = Image.open(io.BytesIO(image_bytes))
            img_format = img.format.lower() if img.format else "jpeg"
            mime_type = f"image/{img_format}"
            logger.debug(f"Determined image format: {img_format}, mime_type: {mime_type}")

            # Add image part using the DECODED BYTES
            prompt_parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_bytes
                }
            })
            logger.info(f"Successfully processed and prepared image part (mime_type: {mime_type})")
        except base64.binascii.Error as e:
            logger.error(f"Base64 decoding error during image processing: {str(e)}")
            return {"error": "Invalid image data", "details": "Could not decode image data. Please ensure it is valid Base64."}
        except Exception as e:
            # Catch potential Pillow errors or other issues
            logger.error(f"Error during image processing (e.g., Pillow): {str(e)}", exc_info=True)
            return {"error": "Image processing error", "details": f"Could not process the uploaded image. Error: {str(e)}"}
    
    # Add text problem if provided
    if problem_text:
        prompt_parts.append({"text": f"Problem: {problem_text}"})
    
    # Add SIMPLIFIED instructions for the model
    instructions = """
    Please provide the following for the STEM problem:
    1. A step-by-step solution.
    2. A simple explanation of the main concepts.
    3. Two similar practice questions.
    
    Structure your response clearly with headings for Solution, Explanation, and Practice Questions.
    """
    logger.debug(f"Using simplified instructions: {instructions}")
    prompt_parts.append({"text": instructions})
    
    # Define safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    # Make API call
    try:
        logger.info(f"Generating content with model: {model.model_name}")
        logger.debug(f"Using safety settings: {safety_settings}")
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_tokens
            ),
            safety_settings=safety_settings # Add safety settings here
        )
        
        # -- Check for blocked response FIRST --
        if not response.candidates:
            logger.warning(f"API response blocked. Prompt Feedback: {response.prompt_feedback}")
            feedback_details = "Unknown reason."
            try:
                 if response.prompt_feedback and response.prompt_feedback.block_reason:
                     feedback_details = f"Reason: {response.prompt_feedback.block_reason}. Safety Ratings: {response.prompt_feedback.safety_ratings}"
                 else:
                     # Log the raw feedback object if reason/ratings aren't directly accessible
                     logger.debug(f"Raw prompt_feedback object: {response.prompt_feedback}")
                     feedback_details = f"No specific block reason provided. Raw Feedback: {response.prompt_feedback}"
            except Exception as fb_error:
                 logger.error(f"Could not parse feedback details: {fb_error}", exc_info=True)
                 feedback_details = f"Could not parse feedback details. Raw Feedback: {response.prompt_feedback}"
                 
            return {"error": "Blocked Response", "details": f"Content blocked by API safety filters. {feedback_details}"}
        # -- End block check --

        # -- Access response text (only if not blocked) --
        try:
            response_text = response.text # Safe now because we know candidates exist
            logger.debug(f"<<< RAW API Response Text >>>\n{response_text}")
        except Exception as e:
            # Catch other potential errors accessing response parts (less likely now)
            logger.error(f"Unexpected error accessing response.text even with candidates: {e}", exc_info=True)
            return {"error": "API Error", "details": "Failed to access valid response content."}
        # -- End access response text --

        logger.info("Successfully received response from Gemini API.")
        
        # --- MODIFIED PARSING LOGIC (No longer strict JSON required) ---
        # We now need to parse the less structured response. This is a placeholder.
        # For now, just return the raw text and let the user see it.
        # A more robust solution would use regex or further prompting to extract sections.
        logger.warning("Parsing logic simplified: Returning raw text as solution due to simplified prompt.")
        return {
            "solution": response_text, 
            "explanation": "(Parsing needed - see solution)", 
            "practice_questions": ["(Parsing needed)", "(Parsing needed)"]
        }
        # --- END MODIFIED PARSING LOGIC ---
            
    except google_exceptions.GoogleAPIError as e:
        logger.error(f"Google API error during generation: {str(e)}")
        return {"error": "Google API error", "details": str(e)}
    except Exception as e:
        # Catch any other unexpected errors during generation
        logger.error(f"Unexpected error during Gemini content generation: {str(e)}", exc_info=True)
        return {"error": "Unexpected error", "details": str(e)} 
