import 'package:flutter/material.dart';
import 'screens/capture_screen.dart';

void main() {
  runApp(const AnimalApp());
}

class AnimalApp extends StatelessWidget {
  const AnimalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Animal Capture',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      // Start directly at CaptureScreen
      home: const CaptureScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
