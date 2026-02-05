import 'package:flutter/material.dart';
import 'package:pec_killer/app.dart';
import 'package:pec_killer/providers/app_providers.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AppProviders(child: PecKillerApp()));
}
