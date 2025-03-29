# STEM Helper

A web application that helps students solve STEM problems by providing step-by-step solutions, simple explanations of underlying concepts, and additional practice problems.

## Features

- Solve STEM problems from text or image input
- Get step-by-step solutions
- Receive simple explanations of the concepts involved
- Get two similar practice problems for additional learning
- Chat-like interface with session history

## Tech Stack

- **Backend**: Python with Flask
- **Frontend**: HTML, CSS, JavaScript
- **LLM**: Google Gemini 2.5 Pro Experimental (`gemini-2.5-pro-exp-03-25`)

## Setup Instructions

### Prerequisites

- Python 3.9+ installed
- Google Gemini API key with access to the `gemini-2.5-pro-exp-03-25` model
- Modern web browser

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd stem_chatbot/backend
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create a `.env` file from the template:
   ```
   cp .env.sample .env
   ```

6. Edit the `.env` file to add your Google Gemini API key and optionally adjust Gemini model parameters:
   ```dotenv
   # .env
   GOOGLE_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY
   
   # Optional: Adjust model parameters (defaults shown)
   # GEMINI_MODEL_NAME=gemini-2.5-pro-exp-03-25
   # GEMINI_TEMPERATURE=0.2
   # GEMINI_MAX_OUTPUT_TOKENS=2048
   
   # Optional: Flask settings
   # PORT=5000
   # FLASK_ENV=development
   ```

7. Start the backend server:
   ```
   python app.py
   ```
   The backend will run on http://localhost:5000

### Frontend Setup

1. The frontend is static HTML, CSS, and JavaScript, so you can simply open the HTML file in your browser or use a simple HTTP server.

2. Using Python's built-in HTTP server (in a separate terminal):
   ```
   cd stem_chatbot/frontend
   python -m http.server 8000
   ```
   The frontend will be accessible at http://localhost:8000

3. Alternatively, you can use extensions like "Live Server" in Visual Studio Code, or any other development server.

## Usage

1. Enter a STEM problem in the text box
2. Or upload an image of a STEM problem by clicking "Upload Image"
3. Click "Solve" to submit the problem
4. View the solution, explanation, and practice problems in the chat interface
5. Continue with additional problems as needed

## API Endpoints

- `GET /api/health`: Health check endpoint
- `POST /api/solve`: Main endpoint for solving STEM problems
  - Request body:
    ```json
    {
      "text_problem": "Solve for x: 2x + 5 = 13",
      "image_data": "[Base64 encoded image data]" // Optional
    }
    ```
  - Response:
    ```json
    {
      "solution": "Step-by-step solution...",
      "explanation": "Simple explanation...",
      "practice_questions": [
        "First practice question...",
        "Second practice question..."
      ]
    }
    ```

## Error Handling & Logging

- The API returns appropriate error responses with details to help troubleshoot issues:
  - 400: Bad request (e.g., missing input, invalid JSON)
  - 500: Server error (e.g., API key issues, Gemini API errors, parsing errors)
- The backend uses Python's `logging` module. Logs are printed to the console with timestamps and levels (INFO, WARNING, ERROR, CRITICAL). In development mode (`FLASK_ENV=development`), the log level is set to DEBUG for more verbose output.

## Project Structure

```
stem_chatbot/
├── backend/               # Python Flask backend
│   ├── app.py             # Main Flask application
│   ├── gemini_client.py   # Gemini API interaction logic
│   ├── requirements.txt   # Python dependencies
│   ├── .env.sample        # Environment variables template
│   └── .gitignore         # Git ignore file
│
├── frontend/              # Web frontend
│   ├── index.html         # Main HTML structure
│   ├── style.css          # CSS styling
│   └── script.js          # JavaScript logic
│
└── README.md              # Project documentation
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your Google Gemini API key is valid and has access to the `gemini-2.5-pro-exp-03-25` model
2. **CORS Errors**: If you see CORS errors in the browser console, ensure the Flask CORS setup is correct
3. **Image Processing**: Large images may cause issues; resize them before uploading
4. **JSON Parsing**: If the model returns non-JSON responses, the client will handle this gracefully

### Debug Steps

1. Check the Flask console for backend errors
2. Check the browser console (F12) for frontend errors
3. Ensure the backend server is running and accessible
4. Verify the API key is set correctly in the `.env` file