import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static const _databaseName = 'pec_killer.db';
  static const _databaseVersion = 1;

  Database? _database;

  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _databaseName);
    return openDatabase(
      path,
      version: _databaseVersion,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE courses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        term TEXT,
        fileNamePattern TEXT
      )
    ''');

    await db.execute('''
      CREATE TABLE assignments (
        id TEXT PRIMARY KEY,
        courseId TEXT NOT NULL,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        dueDate INTEGER,
        status TEXT NOT NULL DEFAULT 'draft',
        targetMinWords INTEGER NOT NULL DEFAULT 1500,
        targetMaxWords INTEGER NOT NULL DEFAULT 3000,
        FOREIGN KEY (courseId) REFERENCES courses(id) ON DELETE CASCADE
      )
    ''');

    await db.execute('''
      CREATE TABLE blocks (
        id TEXT PRIMARY KEY,
        assignmentId TEXT NOT NULL,
        key TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        isDone INTEGER NOT NULL DEFAULT 0,
        sortOrder INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (assignmentId) REFERENCES assignments(id) ON DELETE CASCADE
      )
    ''');

    await db.execute('''
      CREATE TABLE settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        userDisplayName TEXT NOT NULL DEFAULT '',
        lastNameFirst TEXT NOT NULL DEFAULT ''
      )
    ''');

    await db.insert('settings', {
      'id': 1,
      'userDisplayName': '',
      'lastNameFirst': '',
    });
  }

  Future<void> close() async {
    final db = _database;
    if (db != null) {
      await db.close();
      _database = null;
    }
  }
}
