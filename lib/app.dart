import 'package:flutter/material.dart';
import 'package:pec_killer/screens/home_screen.dart';
import 'package:pec_killer/theme/app_theme.dart';

class PecKillerApp extends StatelessWidget {
  const PecKillerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PEC Killer',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system,
      home: const HomeScreen(),
    );
  }
}
