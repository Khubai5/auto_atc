import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

bool? _parseBool(dynamic value) {
  if (value is bool) return value;
  if (value is String) {
    final lower = value.toLowerCase();
    if (lower == 'true') return true;
    if (lower == 'false') return false;
  }
  return null;
}

double? _parseDouble(dynamic value) {
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value);
  return null;
}

class UploadResult {
  UploadResult({
    this.id,
    this.status,
    this.viewType,
    this.filename,
    this.confidence,
    this.arucoDetected,
    this.cmPerPx,
    this.score,
    this.verdict,
    required this.measurements,
    required this.keypoints,
    required this.raw,
  });

  final String? id;
  final String? status;
  final String? viewType;
  final String? filename;
  final double? confidence;
  final bool? arucoDetected;
  final double? cmPerPx;
  final double? score;
  final String? verdict;
  final Map<String, dynamic> measurements;
  final List<Map<String, dynamic>> keypoints;
  final Map<String, dynamic> raw;

  factory UploadResult.fromJson(Map<String, dynamic> json) {
    final measurements = (json['measurements'] as Map<String, dynamic>?) ?? <String, dynamic>{};
    final keypointsRaw = json['keypoints'] as List?;
    final keypoints = keypointsRaw != null
        ? keypointsRaw
            .whereType<Map<String, dynamic>>()
            .toList()
        : <Map<String, dynamic>>[];
    return UploadResult(
      id: json['id']?.toString(),
      status: json['status']?.toString(),
      viewType: json['viewType']?.toString(),
      filename: json['filename']?.toString(),
      confidence: _parseDouble(json['confidence']),
      arucoDetected: _parseBool(json['aruco_detected']),
      cmPerPx: _parseDouble(json['cm_per_px']),
      score: _parseDouble(json['score']),
      verdict: json['verdict']?.toString(),
      measurements: measurements,
      keypoints: keypoints,
      raw: json,
    );
  }
}

class ApiService {
  static const String _baseUrl = 'http://192.168.0.101:8000';
  static const Duration _requestTimeout = Duration(seconds: 60);

  static Future<UploadResult> uploadAnimalData({
    required String animalId,
    required String breed,
    required double weight,
    required String imageBase64,
    required String viewType,
  }) async {
    final Uri uri = Uri.parse('$_baseUrl/upload');
    final Map<String, dynamic> payload = <String, dynamic>{
      'animalID': animalId,
      'breed': breed,
      'weight': weight,
      'imageBase64': imageBase64,
      'viewType': viewType,
    };

    final Map<String, dynamic> json = await _post(uri, payload);
    return UploadResult.fromJson(json);
  }

  static Future<Map<String, dynamic>> finalizeAnimal({
    required String animalId,
    required String breed,
    required double weight,
    String? farmerId,
  }) async {
    final Uri uri = Uri.parse('$_baseUrl/animal/finalize');
    final Map<String, dynamic> payload = <String, dynamic>{
      'animalID': animalId,
      'breed': breed,
      'weight': weight,
    };
    if (farmerId != null && farmerId.isNotEmpty) {
      payload['farmerID'] = farmerId;
    }
    return _post(uri, payload);
  }

  static Future<Map<String, dynamic>> fetchAnimal(String animalId) async {
    final Uri uri = Uri.parse('$_baseUrl/animal/$animalId');
    try {
      final http.Response response = await http
          .get(uri)
          .timeout(_requestTimeout);
      _ensureSuccess(response);
      return _decodeJson(response);
    } on TimeoutException {
      throw Exception('Request timed out after ${_requestTimeout.inSeconds}s');
    } on SocketException catch (e) {
      final msg = e.osError?.message ?? e.message;
      throw Exception('Network error: $msg (${e.osError?.errorCode ?? ''})');
    } on http.ClientException catch (e) {
      throw Exception('Connection error: ${e.message}');
    }
  }

  static Future<Map<String, dynamic>> _post(
    Uri uri,
    Map<String, dynamic> payload,
  ) async {
    try {
      final http.Response response = await http
          .post(
            uri,
            headers: const <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(_requestTimeout);
      _ensureSuccess(response);
      return _decodeJson(response);
    } on TimeoutException {
      throw Exception('Request timed out after ${_requestTimeout.inSeconds}s');
    } on SocketException catch (e) {
      final msg = e.osError?.message ?? e.message;
      throw Exception('Network error: $msg (${e.osError?.errorCode ?? ''})');
    } on http.ClientException catch (e) {
      throw Exception('Connection error: ${e.message}');
    }
  }

  static void _ensureSuccess(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Server responded ${response.statusCode}: ${response.body}');
    }
  }

  static Map<String, dynamic> _decodeJson(http.Response response) {
    if (response.body.isEmpty) {
      return const <String, dynamic>{};
    }
    final dynamic decoded = jsonDecode(response.body);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    throw Exception('Unexpected response format: ${response.body}');
  }
}
