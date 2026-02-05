import 'package:pec_killer/database/database_helper.dart';
import 'package:pec_killer/models/settings.dart';

class SettingsRepository {
  final DatabaseHelper _db;

  SettingsRepository(this._db);

  Future<UserSettings> get() async {
    final db = await _db.database;
    final maps = await db.query('settings', where: 'id = 1');
    if (maps.isEmpty) return const UserSettings();
    return UserSettings.fromMap(maps.first);
  }

  Future<void> update(UserSettings settings) async {
    final db = await _db.database;
    await db.update(
      'settings',
      {...settings.toMap(), 'id': 1},
      where: 'id = 1',
    );
  }
}
