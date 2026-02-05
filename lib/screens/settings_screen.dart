import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:pec_killer/database/settings_repository.dart';
import 'package:pec_killer/models/settings.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _displayNameCtrl;
  late TextEditingController _lastNameFirstCtrl;
  bool _loading = true;
  bool _saved = false;

  @override
  void initState() {
    super.initState();
    _displayNameCtrl = TextEditingController();
    _lastNameFirstCtrl = TextEditingController();
    _load();
  }

  @override
  void dispose() {
    _displayNameCtrl.dispose();
    _lastNameFirstCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final settings = await context.read<SettingsRepository>().get();
    if (mounted) {
      setState(() {
        _displayNameCtrl.text = settings.userDisplayName;
        _lastNameFirstCtrl.text = settings.lastNameFirst;
        _loading = false;
      });
    }
  }

  Future<void> _save() async {
    final settings = UserSettings(
      userDisplayName: _displayNameCtrl.text.trim(),
      lastNameFirst: _lastNameFirstCtrl.text.trim(),
    );
    await context.read<SettingsRepository>().update(settings);
    if (mounted) {
      setState(() => _saved = true);
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Configuración guardada')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Configuración')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Datos del estudiante',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _displayNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre completo',
                    hintText: 'Ej: Juan García López',
                    helperText: 'Se muestra en el PDF exportado',
                  ),
                  textCapitalization: TextCapitalization.words,
                  onChanged: (_) =>
                      setState(() => _saved = false),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _lastNameFirstCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Apellido + Nombre (para archivo)',
                    hintText: 'Ej: GarcíaLópezJuan',
                    helperText:
                        'Se usa en el nombre del archivo: CURSO_PEC2_GarcíaLópezJuan.pdf',
                  ),
                  onChanged: (_) =>
                      setState(() => _saved = false),
                ),
                const SizedBox(height: 32),
                FilledButton(
                  onPressed: _saved ? null : _save,
                  child: Text(_saved ? 'Guardado' : 'Guardar'),
                ),
                const SizedBox(height: 32),
                const Divider(),
                const SizedBox(height: 16),
                Text('Acerca de',
                    style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text('PEC Killer v1.0.0',
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 4),
                Text(
                    'Pipeline de entregas para estudiantes de la UOC.',
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 4),
                Text('Offline-first. Sin IA. Sin cloud.',
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
    );
  }
}
