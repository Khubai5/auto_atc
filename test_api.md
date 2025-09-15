# API Testing Examples

## Environment Setup

Create a `.env` file in the project root:
```bash
MONGO_URI=mongodb://localhost:27017/
DB_NAME=animal_atc
```

Or for MongoDB Atlas:
```bash
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=animal_atc
```

## Test Commands

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. Upload Animal Data (Front View)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "front"
  }'
```

### 3. Upload Animal Data (Side View)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "side"
  }'
```

### 4. Upload Animal Data (Rear View)
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW001",
    "breed": "Holstein",
    "weight": 650.5,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "rear"
  }'
```

### 5. Get Animal Record
```bash
curl -X GET "http://localhost:8000/animal/COW001"
```

### 6. Upload Different Animal
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "animalID": "COW002",
    "breed": "Angus",
    "weight": 750.0,
    "imageBase64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "viewType": "front"
  }'
```

## Expected Responses

### Upload Response
```json
{
  "id": "COW001",
  "status": "saved"
}
```

### Get Animal Response
```json
{
  "animalID": "COW001",
  "breed": "Holstein",
  "weight": 650.5,
  "farmerID": null,
  "views": [
    {
      "viewType": "front",
      "filename": "front_12345678-1234-1234-1234-123456789abc.jpg",
      "uploaded_at": "2024-01-15T10:30:00.000Z",
      "confidence": 0.85
    },
    {
      "viewType": "side",
      "filename": "side_87654321-4321-4321-4321-cba987654321.jpg",
      "uploaded_at": "2024-01-15T10:31:00.000Z",
      "confidence": 0.92
    }
  ],
  "measurements": {},
  "score": 8.7,
  "verdict": "VG",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## File Structure After Uploads
```
uploads/
├── COW001/
│   ├── front_12345678-1234-1234-1234-123456789abc.jpg
│   ├── side_87654321-4321-4321-4321-cba987654321.jpg
│   └── rear_11111111-2222-3333-4444-555555555555.jpg
└── COW002/
    └── front_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jpg
```
