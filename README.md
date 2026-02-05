# PEC Killer

**Assignment pipeline for UOC students.** A mobile-first app that takes you from
assignment creation to export-ready submission, faster than Notion and with fewer
decisions.

## What's Implemented (MVP)

### Courses (Asignaturas)
- Create, edit, delete courses
- Optional semester/term and filename pattern per course

### Assignments (PECs)
- Create assignments per course with type (Comentario crítico / Ensayo)
- Due date, status tracking (Borrador → En progreso → Revisión → Entregado)
- List view by course with status badges
- Home screen shows upcoming deadlines

### Template-Based Editor
- Fixed block structure per assignment type (no freeform pages)
- Each block: title, text content, notes field, done toggle
- Live word count per block and total
- Two templates implemented:
  - **Comentario crítico**: Tesis → Resumen → Conceptos clave → Argumentos del
    autor → Crítica → Implicaciones → Conclusión → Referencias
  - **Ensayo**: Pregunta + postura → Roadmap → Argumento 1 → Argumento 2 →
    Contraargumento + refutación → Síntesis → Conclusión + límites → Referencias

### Delivery Mode (Killer Feature)
- Pre-submission checklist with strict validation:
  - Due date is set
  - Thesis/pregunta block is not empty
  - All required blocks have content
  - Minimum citation markers detected (pattern: `(Author, Year)`)
  - Total word count within user-defined target range
- Clear pass/fail indicators with actionable fix suggestions

### Export
- PDF generation with clean academic formatting
- Configurable filename: `COURSE_PEC2_LastNameName.pdf`
- Submission package as ZIP (PDF + plaintext checklist report)

### Settings
- User display name (for filename generation)
- All data stored locally (offline-first, no cloud)

## How to Run

```bash
# Prerequisites: Flutter SDK 3.10+
flutter pub get
flutter run          # with connected Android device or emulator

# Run tests
flutter test
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Flutter** | Cross-platform but Android-first. Single codebase, Material 3 native. |
| **sqflite (SQLite)** | Most mature offline DB for Flutter. No codegen, relational queries, battle-tested. |
| **Provider** | Minimal DI for repositories. Screens own their state via StatefulWidget. |
| **No code generation** | Faster iteration for MVP. Manual serialization is fine for 4 models. |
| **Fixed templates** | Core UX decision: prevents over-customization, keeps students on track. |
| **No AI, no cloud, no collab** | MVP scope constraint. Offline-first, deterministic, simple. |

## What Is Intentionally NOT Implemented

- AI writing assistance or suggestions
- Cloud sync / account system
- Real-time collaboration
- Plugin/extension architecture
- Custom block types or freeform pages
- Rich text formatting beyond plain text
- iOS-specific polish (works but not optimized)
- Calendar view for assignments (list only in MVP)
- Notifications / reminders

## Architecture

```
lib/
├── main.dart                 # Entry point
├── app.dart                  # MaterialApp + routing
├── models/                   # Data classes (Course, Assignment, Block, Settings)
├── database/                 # SQLite helper + repository layer
├── services/                 # Business logic (templates, validation, export, word count)
├── screens/                  # Full-page UI widgets
├── widgets/                  # Reusable UI components
├── theme/                    # Material 3 theme configuration
└── providers/                # Provider setup for DI
```

## Next Milestones (ordered by impact)

1. **Calendar view** for assignments by due date
2. **Board view** (Kanban-style) for assignments by status
3. **Push notifications** for upcoming deadlines
4. **Cloud backup** (optional, encrypted, user-controlled)
5. **Rich text** in blocks (bold, italic, bullet lists)
6. **Custom templates** (user can create new assignment types)
7. **Statistics dashboard** (words written, assignments completed, streaks)
8. **iOS polish** (Cupertino adaptations, App Store release)
