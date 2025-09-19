# Animal ATC FastAPI Backend

A minimal FastAPI backend that matches the Flutter app requirements for animal data upload and scoring.

## Features

- **POST /upload** endpoint that accepts animal data with image
- Base64 image decoding and local storage
- Scoring system with verdict classification
- CORS support for Flutter app integration

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Or run directly:
   ```bash
   python main.py
   ```

## API Endpoints

### POST /upload
Accepts JSON payload:
```json
{
  "animalID": "string",
  "breed": "string", 
  "weight": 12.5,
  "imageBase64": "base64_encoded_image_string"
}
```

Returns JSON response:
```json
{
  "score": 8.7,
  "verdict": "VG"
}
```

### Scoring System
- **EX**: score > 9
- **VG**: 8 < score ≤ 9  
- **GP**: 7 < score ≤ 8
- **G**: 6 < score ≤ 7
- **Poor**: score ≤ 6

## File Structure
```
.
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── uploads/            # Directory for saved images (auto-created)
└── README.md           # This file
```

## Notes
- Images are saved to `./uploads/` directory with format: `{animalID}_{timestamp}.jpg`
- The server runs on `http://0.0.0.0:8000` by default
- CORS is enabled for cross-origin requests from Flutter app
