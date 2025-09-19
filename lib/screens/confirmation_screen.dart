import 'package:flutter/material.dart';

class ConfirmationScreen extends StatelessWidget {
  const ConfirmationScreen({super.key, required this.record});

  final Map<String, dynamic> record;

  double? get _score => _asDouble(record['score']);
  String? get _verdict => record['verdict']?.toString();
  Map<String, dynamic> get _measurements =>
      (record['measurements'] as Map<String, dynamic>?) ?? <String, dynamic>{};
  List<Map<String, dynamic>> get _views =>
      (record['views'] as List?)?.whereType<Map<String, dynamic>>().toList() ?? <Map<String, dynamic>>[];

  static double? _asDouble(dynamic value) =>
      value is num ? value.toDouble() : (value is String ? double.tryParse(value) : null);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assessment Complete'),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                color: Colors.green.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.green.shade600),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Animal assessment completed successfully!',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Score', style: TextStyle(color: Colors.black54)),
                            Text(
                              _score?.toStringAsFixed(1) ?? '-',
                              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                    color: _getScoreColor(_score),
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Verdict', style: TextStyle(color: Colors.black54)),
                            Text(
                              _verdict ?? '-',
                              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                    color: _getVerdictColor(_verdict),
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              if (_measurements.isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Measurements',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        ..._measurements.entries.map(
                          (entry) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2.0),
                            child: Text('${entry.key}: ${entry.value}'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              if (_views.isNotEmpty) ...[
                const SizedBox(height: 16),
                const Text(
                  'View Breakdown',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ..._views.map((view) {
                  final viewType = view['viewType']?.toString() ?? 'view';
                  final viewScore = _asDouble(view['score']);
                  final viewVerdict = view['verdict']?.toString();
                  final cmPerPx = _asDouble(view['cm_per_px']);
                  final measurements =
                      (view['measurements'] as Map<String, dynamic>?) ?? <String, dynamic>{};
                  final uploadedAt = view['uploaded_at']?.toString();

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12.0),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              viewType.toUpperCase(),
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            if (uploadedAt != null) ...[
                              const SizedBox(height: 4),
                              Text('Captured: $uploadedAt', style: const TextStyle(color: Colors.black54)),
                            ],
                            if (cmPerPx != null)
                              Text('Scale: ${cmPerPx.toStringAsFixed(4)} cm/px'),
                            if (viewScore != null)
                              Text('View score: ${viewScore.toStringAsFixed(1)} (${viewVerdict ?? '-'})'),
                            if (measurements.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              const Text('Measurements:', style: TextStyle(fontWeight: FontWeight.w600)),
                              ...measurements.entries.map(
                                (entry) => Text('${entry.key}: ${entry.value}'),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  );
                }),
              ],
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
                      icon: const Icon(Icons.home),
                      label: const Text('New Assessment'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Results saved to device')),
                        );
                      },
                      icon: const Icon(Icons.save),
                      label: const Text('Save Results'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getScoreColor(double? score) {
    if (score == null) return Colors.grey;
    if (score > 9) return Colors.purple;
    if (score > 8) return Colors.blue;
    if (score > 7) return Colors.green;
    if (score > 6) return Colors.orange;
    return Colors.red;
  }

  Color _getVerdictColor(String? verdict) {
    switch (verdict?.toUpperCase()) {
      case 'EX':
        return Colors.purple;
      case 'VG':
        return Colors.blue;
      case 'GP':
        return Colors.green;
      case 'G':
        return Colors.orange;
      case 'POOR':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
