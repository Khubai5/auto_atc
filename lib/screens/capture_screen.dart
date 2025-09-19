import 'dart:convert';

import 'dart:io';

import 'dart:typed_data';



import 'package:camera/camera.dart';

import 'package:image_picker/image_picker.dart';

import 'package:flutter/material.dart';

import 'package:uuid/uuid.dart';

import 'package:image/image.dart' as img;



import '../services/api_service.dart';

import 'form_screen.dart';



enum ViewType { front, side, rear }



class CaptureScreen extends StatefulWidget {

  const CaptureScreen({super.key});



  @override

  State<CaptureScreen> createState() => _CaptureScreenState();

}



class _CaptureScreenState extends State<CaptureScreen> {

  CameraController? _cameraController;

  List<CameraDescription>? _cameras;

  bool _isInitialized = false;

  bool _isCapturing = false;

  final ImagePicker _imagePicker = ImagePicker();

  

  int _currentStep = 0;

  final List<ViewType> _viewTypes = [ViewType.front, ViewType.side, ViewType.rear];

  final Map<ViewType, File> _capturedImages = {};

  final Map<ViewType, UploadResult> _uploadResults = {};

  

  double _overlayOpacity = 0.5;

  final String _animalId = const Uuid().v4();



  @override

  void initState() {

    super.initState();

    _initializeCamera();

  }



  Future<void> _initializeCamera() async {

    try {

      _cameras = await availableCameras();

      if (_cameras!.isNotEmpty) {

        _cameraController = CameraController(

          _cameras![0],

          ResolutionPreset.medium,

          enableAudio: false,

        );

        await _cameraController!.initialize();

        setState(() {

          _isInitialized = true;

        });

      }

    } catch (e) {

      print('Error initializing camera: $e');

    }

  }



  @override

  void dispose() {

    _cameraController?.dispose();

    super.dispose();

  }



  ViewType get _currentViewType => _viewTypes[_currentStep];



  String get _overlayAsset {

    switch (_currentViewType) {

      case ViewType.front:

        return 'assets/overlays/front_overlay.png';

      case ViewType.side:

        return 'assets/overlays/side_overlay.png';

      case ViewType.rear:

        return 'assets/overlays/rear_overlay.png';

    }

  }



  String get _viewTypeName {

    switch (_currentViewType) {

      case ViewType.front:

        return 'Front';

      case ViewType.side:

        return 'Side';

      case ViewType.rear:

        return 'Rear';

    }

  }



  Future<void> _captureImage() async {

    if (_cameraController == null || !_cameraController!.value.isInitialized) return;

    final ViewType capturedView = _currentViewType;



    setState(() {

      _isCapturing = true;

    });



    try {

      final XFile image = await _cameraController!.takePicture();

      final File imageFile = File(image.path);

      

      setState(() {

        _capturedImages[capturedView] = imageFile;

      });



      // Upload the image

      await _uploadImage(imageFile, capturedView);

      

    } catch (e) {

      ScaffoldMessenger.of(context).showSnackBar(

        SnackBar(content: Text('Capture failed: $e')),

      );

    } finally {

      setState(() {

        _isCapturing = false;

      });

    }

  }



  Future<void> _pickFromGallery() async {

    final ViewType targetView = _currentViewType;

    setState(() {

      _isCapturing = true;

    });



    try {

      final XFile? picked = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 100,
      );

      if (picked == null) {

        return;

      }

      final File imageFile = File(picked.path);

      setState(() {

        _capturedImages[targetView] = imageFile;

      });

      await _uploadImage(imageFile, targetView, preserveOriginal: true);

    } catch (e) {

      if (mounted) {

        ScaffoldMessenger.of(context).showSnackBar(

          SnackBar(content: Text('Upload failed: $e')),

        );

      }

    } finally {

      if (mounted) {

        setState(() {

          _isCapturing = false;

        });

      }

    }

  }



  Future<void> _uploadImage(File imageFile, ViewType viewType, {bool preserveOriginal = false}) async {

    final ViewType completedView = viewType;

    try {

      final Uint8List imageBytes = await imageFile.readAsBytes();

      img.Image? decoded;
      try {
        decoded = img.decodeImage(imageBytes);
      } catch (_) {
        decoded = null;
      }

      if (decoded != null) {
        print('Upload ${completedView.name}: ${decoded.width}x${decoded.height}px');
      } else {
        print('Upload ${completedView.name}: dimensions unavailable (decode failed)');
      }

      // Preserve gallery images at full resolution; compress camera captures.
      String imageBase64;
      if (preserveOriginal) {
        imageBase64 = base64Encode(imageBytes);
      } else {
        try {
          if (decoded != null) {
            // Resize longest side to 1280px, keep aspect ratio
            const int maxSize = 1280;
            final bool isLandscape = decoded.width >= decoded.height;
            final int targetWidth = isLandscape
                ? maxSize
                : (decoded.width * maxSize / decoded.height).round();
            final int targetHeight = isLandscape
                ? (decoded.height * maxSize / decoded.width).round()
                : maxSize;
            final img.Image resized = img.copyResize(
              decoded,
              width: targetWidth,
              height: targetHeight,
              interpolation: img.Interpolation.cubic,
            );
            final List<int> jpg = img.encodeJpg(resized, quality: 85);
            imageBase64 = base64Encode(jpg);
          } else {
            imageBase64 = base64Encode(imageBytes);
          }
        } catch (_) {
          // Fallback to original if compression fails
          imageBase64 = base64Encode(imageBytes);
        }
      }
      final UploadResult result = await ApiService.uploadAnimalData(

        animalId: _animalId,

        breed: 'Unknown', // Will be updated in form screen

        weight: 0.0, // Will be updated in form screen

        imageBase64: imageBase64,

        viewType: completedView.name,

      );

      print('ArUco detection (${completedView.name}): detected=${result.arucoDetected} cm_per_px=${result.cmPerPx}');



      if (mounted) {

        setState(() {

          _uploadResults[completedView] = result;

        });

      }



      // Move to next step or complete

      if (_currentStep < _viewTypes.length - 1) {

        setState(() {

          _currentStep++;

        });

      } else {

        // All captures complete, navigate to form screen

        _navigateToForm();

      }

      

    } catch (e) {

      ScaffoldMessenger.of(context).showSnackBar(

        SnackBar(content: Text('Upload failed: $e')),

      );

    }

  }



  void _navigateToForm() {

    Navigator.of(context).pushReplacement(

      MaterialPageRoute(

        builder: (_) => FormScreen(

          animalId: _animalId,

          uploadResults: _uploadResults.map(

            (view, result) => MapEntry(view.name, result),

          ),

        ),

      ),

    );

  }



  void _previousStep() {

    if (_currentStep > 0) {

      setState(() {

        _currentStep--;

      });

    }

  }



  Widget _buildCameraPreview() {

    if (!_isInitialized || _cameraController == null) {

      return const Center(

        child: CircularProgressIndicator(),

      );

    }



    return Stack(

      children: [

        // Camera preview

        SizedBox(

          width: double.infinity,

          height: double.infinity,

          child: CameraPreview(_cameraController!),

        ),

        

        // Overlay

        Positioned.fill(

          child: Opacity(

            opacity: _overlayOpacity,

            child: Image.asset(

              _overlayAsset,

              fit: BoxFit.cover,

              errorBuilder: (context, error, stackTrace) {

                // Fallback overlay if image not found

                return _buildFallbackOverlay();

              },

            ),

          ),

        ),

        

        // ArUco marker guidance

        Positioned(

          bottom: 20,

          left: 20,

          child: Container(

            padding: const EdgeInsets.all(8),

            decoration: BoxDecoration(

              color: Colors.black54,

              borderRadius: BorderRadius.circular(8),

            ),

            child: const Text(

              'Place ArUco marker at bottom-left (10cm printed)',

              style: TextStyle(color: Colors.white, fontSize: 12),

            ),

          ),

        ),

        

        // ArUco marker guide box

        Positioned(

          bottom: 20,

          left: 20,

          child: Container(

            width: 60,

            height: 60,

            decoration: BoxDecoration(

              border: Border.all(color: Colors.yellow, width: 2),

              borderRadius: BorderRadius.circular(4),

            ),

          ),

        ),

      ],

    );

  }



  Widget _buildFallbackOverlay() {

    return Container(

      color: Colors.transparent,

      child: Center(

        child: Container(

          width: 200,

          height: 300,

          decoration: BoxDecoration(

            border: Border.all(color: Colors.white, width: 3),

            borderRadius: BorderRadius.circular(8),

          ),

          child: Center(

            child: Text(

              '${_viewTypeName} View\nGuide Box',

              textAlign: TextAlign.center,

              style: const TextStyle(

                color: Colors.white,

                fontSize: 16,

                fontWeight: FontWeight.bold,

              ),

            ),

          ),

        ),

      ),

    );

  }



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      appBar: AppBar(

        title: Text('Capture ${_viewTypeName} View'),

        leading: _currentStep > 0

            ? IconButton(

                icon: const Icon(Icons.arrow_back),

                onPressed: _previousStep,

              )

            : null,

      ),

      body: Column(

        children: [

          // Progress indicator

          LinearProgressIndicator(

            value: (_currentStep + 1) / _viewTypes.length,

          ),

          

          // Camera preview with overlay

          Expanded(

            flex: 4,

            child: _buildCameraPreview(),

          ),

          

          // Instructions

          Container(

            padding: const EdgeInsets.all(16),

            child: Column(

              children: [

                Text(

                  'Step ${_currentStep + 1} of ${_viewTypes.length}',

                  style: Theme.of(context).textTheme.titleMedium,

                ),

                const SizedBox(height: 8),

                const Text(

                  'Align animal + ArUco marker in guide box',

                  style: TextStyle(color: Colors.black54),

                ),

                const SizedBox(height: 16),

                

                // Overlay opacity control

                Row(

                  children: [

                    const Text('Overlay Opacity:'),

                    Expanded(

                      child: Slider(

                        value: _overlayOpacity,

                        min: 0.0,

                        max: 1.0,

                        divisions: 10,

                        onChanged: (value) {

                          setState(() {

                            _overlayOpacity = value;

                          });

                        },

                      ),

                    ),

                    Text('${(_overlayOpacity * 100).round()}%'),

                  ],

                ),

              ],

            ),

          ),

          

          // Capture / Upload actions

          Container(

            padding: const EdgeInsets.all(16),

            child: Row(

              children: [

                Expanded(

                  child: FilledButton.icon(

                    onPressed: _isCapturing ? null : _captureImage,

                    icon: _isCapturing

                        ? const SizedBox(

                            width: 20,

                            height: 20,

                            child: CircularProgressIndicator(strokeWidth: 2),

                          )

                        : const Icon(Icons.camera_alt),

                    label: Text(_isCapturing ? 'Capturing...' : 'Capture ${_viewTypeName}'),

                  ),

                ),

                const SizedBox(width: 12),

                Expanded(

                  child: OutlinedButton.icon(

                    onPressed: _isCapturing ? null : _pickFromGallery,

                    icon: const Icon(Icons.photo_library_outlined),

                    label: Text(_isCapturing ? 'Please wait...' : 'Upload ${_viewTypeName}'),

                  ),

                ),

              ],

            ),

          ),

        ],

      ),

    );

  }

}




