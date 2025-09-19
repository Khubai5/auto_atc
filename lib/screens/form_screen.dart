import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'confirmation_screen.dart';

class FormScreen extends StatefulWidget {
  const FormScreen({
    super.key,
    required this.animalId,
    this.uploadResults = const {},
  });

  final String animalId;
  final Map<String, UploadResult> uploadResults;

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final TextEditingController _breedController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();
  final TextEditingController _farmerController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    _breedController.dispose();
    _weightController.dispose();
    _farmerController.dispose();
    super.dispose();
  }

  List<Widget> _buildDetectionDetails() {
    if (widget.uploadResults.isEmpty) {
      return const [
        SizedBox(height: 12),
        Text(
          'No view results available. Please upload images first.',
          style: TextStyle(color: Colors.redAccent),
        ),
      ];
    }

    const Map<String, String> labels = {
      'front': 'Front View',
      'side': 'Side View',
      'rear': 'Rear View',
    };

    final List<Widget> cards = <Widget>[];
    final entries = widget.uploadResults.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));

    for (final entry in entries) {
      final UploadResult result = entry.value;
      final String title = labels[entry.key] ?? entry.key;
      final bool detected = result.arucoDetected == true;
      final measurements = result.measurements;
      final measureWidgets = measurements.entries.map((e) => Text('${e.key}: ${e.value}')).toList();

      cards
        ..add(
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  Text('ArUco: ${detected ? 'Detected' : 'Not detected'}'),
                  if (result.cmPerPx != null)
                    Text('Scale: ${result.cmPerPx!.toStringAsFixed(4)} cm/px'),
                  if (result.confidence != null)
                    Text('Avg confidence: ${(result.confidence! * 100).toStringAsFixed(1)}%'),
                  if (result.score != null)
                    Text('View score: ${result.score!.toStringAsFixed(1)}  (${result.verdict ?? '-'})'),
                  if (measureWidgets.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    const Text('Measurements:', style: TextStyle(fontWeight: FontWeight.w600)),
                    ...measureWidgets,
                  ],
                ],
              ),
            ),
          ),
        )
        ..add(const SizedBox(height: 8));
    }
    cards.removeLast();
    return cards;
  }

  Future<void> _submit() async {
    final String breed = _breedController.text.trim();
    final String weightText = _weightController.text.trim();
    final String farmerId = _farmerController.text.trim();

    if (breed.isEmpty || weightText.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter breed and weight.')),
      );
      return;
    }
    final double? weight = double.tryParse(weightText);
    if (weight == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Weight must be a number.')),
      );
      return;
    }
    if (widget.uploadResults.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please upload all views before finalising.')),
      );
      return;
    }

    setState(() {
      _submitting = true;
    });

    try {
      final record = await ApiService.finalizeAnimal(
        animalId: widget.animalId,
        breed: breed,
        weight: weight,
        farmerId: farmerId.isEmpty ? null : farmerId,
      );

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ConfirmationScreen(record: record),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Enter Animal Details')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Capture Complete!',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Animal ID: ${widget.animalId}',
                      style: const TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 4),
                    const Text('Captured view results:'),
                    const SizedBox(height: 12),
                    ..._buildDetectionDetails(),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _breedController,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Breed',
                hintText: 'e.g., Holstein, Angus',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _weightController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Weight (kg)',
                hintText: 'e.g., 650.5',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _farmerController,
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(
                labelText: 'Farmer ID (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const Spacer(),
            FilledButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.check),
              label: Text(_submitting ? 'Processing...' : 'Complete Assessment'),
            ),
          ],
        ),
      ),
    );
  }
}
