# Flutter Multi-View Animal Capture App

A Flutter application for capturing multiple views of animals with overlay guidance and ArUco marker detection support.

## Features

### 🎯 Multi-View Capture System
- **Front View**: Capture animal from the front
- **Side View**: Capture animal from the side  
- **Rear View**: Capture animal from the rear
- **Stepper Interface**: Guided 3-step capture process
- **Progress Indicator**: Visual progress through capture steps

### 📷 Camera Integration
- **Live Camera Preview**: Real-time camera feed using `camera` package
- **Overlay System**: Semi-transparent PNG overlays for guidance
- **Opacity Control**: Adjustable overlay transparency (0-100%)
- **Fallback Overlays**: Built-in fallback when overlay images are missing

### 🎯 ArUco Marker Guidance
- **Visual Guide Box**: Yellow rectangle in bottom-left corner
- **Instruction Text**: "Place ArUco marker at bottom-left (10cm printed)"
- **Marker Detection**: Backend handles actual marker detection and cm_per_px calculation

### 🔄 Backend Integration
- **Real-time Upload**: Images uploaded immediately after capture
- **View Type Support**: Each capture includes viewType (front/side/rear)
- **MongoDB Storage**: Images stored with organized directory structure
- **Error Handling**: Comprehensive error handling and user feedback

## App Flow

1. **Capture Screen**: Multi-step camera capture with overlays
2. **Form Screen**: Enter animal details (breed, weight)
3. **Confirmation Screen**: Display assessment results

## File Structure

```
lib/
├── main.dart                 # App entry point
├── screens/
│   ├── capture_screen.dart  # Multi-view camera capture
│   ├── form_screen.dart     # Animal details form
│   └── confirmation_screen.dart # Results display
└── services/
    └── api_service.dart     # Backend API integration

assets/overlays/
├── front_overlay.png        # Front view guidance overlay
├── side_overlay.png         # Side view guidance overlay
└── rear_overlay.png         # Rear view guidance overlay
```

## Dependencies

```yaml
dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6
  image_picker: ^1.1.2
  http: ^0.13.6
  uuid: ^4.4.0
  camera: ^0.10.5+9
```

## Setup Instructions

### 1. Install Dependencies
```bash
flutter pub get
```

### 2. Camera Permissions
Add camera permissions to your platform-specific files:

**Android** (`android/app/src/main/AndroidManifest.xml`):
```xml
<uses-permission android:name="android.permission.CAMERA" />
```

**iOS** (`ios/Runner/Info.plist`):
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to capture animal images</string>
```

### 3. Overlay Images
Place your custom overlay images in `assets/overlays/`:
- `front_overlay.png` - Front view guidance
- `side_overlay.png` - Side view guidance  
- `rear_overlay.png` - Rear view guidance

**Overlay Specifications:**
- Format: PNG with transparency
- Resolution: 1080x1920 (portrait)
- Content: Semi-transparent guide showing animal positioning
- ArUco Marker: Small square in bottom-left corner

### 4. Backend Configuration
Update the API base URL in `lib/services/api_service.dart`:
```dart
static const String _baseUrl = 'http://YOUR_BACKEND_URL:8000';
```

## Usage

### Multi-View Capture
1. **Front View**: Position animal in guide box, capture
2. **Side View**: Rotate to side, position in guide box, capture  
3. **Rear View**: Rotate to rear, position in guide box, capture
4. **ArUco Marker**: Place 10cm printed marker in yellow guide box

### Overlay Controls
- **Opacity Slider**: Adjust overlay transparency (0-100%)
- **Fallback Mode**: Automatic fallback when overlay images missing
- **Visual Guide**: White rectangle shows animal positioning area

### Error Handling
- **Camera Errors**: Graceful fallback and user notification
- **Upload Errors**: Retry mechanism and error messages
- **Network Issues**: Clear error feedback to user

## Backend Integration

### API Endpoints
- `POST /upload` - Upload animal image with view type
- `GET /animal/{animalID}` - Retrieve animal record

### Request Format
```json
{
  "animalID": "uuid-string",
  "breed": "Holstein",
  "weight": 650.5,
  "imageBase64": "base64-encoded-image",
  "viewType": "front|side|rear"
}
```

### Response Format
```json
{
  "id": "animal-id",
  "status": "saved"
}
```

## Development Notes

### Overlay System
- Overlays are PNG images with transparency
- Positioned using `Stack` widget over camera preview
- Opacity controlled by `Opacity` widget
- Fallback overlays generated programmatically

### Camera Handling
- Uses `camera` package for live preview
- High resolution capture (ResolutionPreset.high)
- Audio disabled for image capture
- Proper disposal of camera resources

### State Management
- Local state management with `StatefulWidget`
- Step tracking for multi-view capture
- Image storage in local `Map<ViewType, File>`
- Progress tracking through capture steps

## Customization

### Overlay Images
Replace placeholder overlays in `assets/overlays/` with your custom designs:
- Maintain 1080x1920 resolution
- Include ArUco marker guide in bottom-left
- Use semi-transparent design
- Test with different device orientations

### UI Theming
Modify `lib/main.dart` to customize app theme:
```dart
theme: ThemeData(
  colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
  useMaterial3: true,
),
```

### Backend URL
Update API endpoint in `lib/services/api_service.dart`:
```dart
static const String _baseUrl = 'http://YOUR_SERVER:PORT';
```

## Troubleshooting

### Camera Issues
- Check camera permissions
- Ensure device has working camera
- Test on physical device (camera doesn't work in simulator)

### Overlay Issues
- Verify overlay images are in correct directory
- Check PNG format and transparency
- Ensure proper asset registration in `pubspec.yaml`

### Backend Connection
- Verify backend server is running
- Check network connectivity
- Validate API endpoint URL
- Review backend logs for errors

## Future Enhancements

- [ ] Offline mode with local storage
- [ ] Image preview before upload
- [ ] Retry failed uploads
- [ ] Batch upload capability
- [ ] Custom overlay editor
- [ ] Advanced camera controls (flash, focus)
- [ ] Image quality validation
- [ ] GPS location tagging
