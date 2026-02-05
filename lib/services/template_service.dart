import 'package:pec_killer/models/assignment.dart';
import 'package:pec_killer/models/block.dart';
import 'package:uuid/uuid.dart';

class TemplateDefinition {
  final String key;
  final String title;

  const TemplateDefinition({required this.key, required this.title});
}

class TemplateService {
  static const _uuid = Uuid();

  static const List<TemplateDefinition> comentarioCriticoTemplate = [
    TemplateDefinition(key: 'tesis', title: 'Tesis'),
    TemplateDefinition(key: 'resumen', title: 'Resumen'),
    TemplateDefinition(key: 'conceptos_clave', title: 'Conceptos clave'),
    TemplateDefinition(key: 'argumentos_autor', title: 'Argumentos del autor'),
    TemplateDefinition(key: 'critica', title: 'Crítica'),
    TemplateDefinition(key: 'implicaciones', title: 'Implicaciones'),
    TemplateDefinition(key: 'conclusion', title: 'Conclusión'),
    TemplateDefinition(key: 'referencias', title: 'Referencias'),
  ];

  static const List<TemplateDefinition> ensayoTemplate = [
    TemplateDefinition(key: 'pregunta_postura', title: 'Pregunta + postura'),
    TemplateDefinition(key: 'roadmap', title: 'Roadmap'),
    TemplateDefinition(key: 'argumento_1', title: 'Argumento 1'),
    TemplateDefinition(key: 'argumento_2', title: 'Argumento 2'),
    TemplateDefinition(
        key: 'contraargumento', title: 'Contraargumento + refutación'),
    TemplateDefinition(key: 'sintesis', title: 'Síntesis'),
    TemplateDefinition(
        key: 'conclusion_limites', title: 'Conclusión + límites'),
    TemplateDefinition(key: 'referencias', title: 'Referencias'),
  ];

  static List<TemplateDefinition> getTemplate(AssignmentType type) {
    switch (type) {
      case AssignmentType.comentarioCritico:
        return comentarioCriticoTemplate;
      case AssignmentType.ensayo:
        return ensayoTemplate;
    }
  }

  /// The first block key that acts as the "thesis" for validation purposes.
  static String getThesisKey(AssignmentType type) {
    switch (type) {
      case AssignmentType.comentarioCritico:
        return 'tesis';
      case AssignmentType.ensayo:
        return 'pregunta_postura';
    }
  }

  /// Creates Block instances for a new assignment from the template.
  static List<Block> createBlocks(String assignmentId, AssignmentType type) {
    final template = getTemplate(type);
    return template.asMap().entries.map((entry) {
      return Block(
        id: _uuid.v4(),
        assignmentId: assignmentId,
        key: entry.value.key,
        title: entry.value.title,
        sortOrder: entry.key,
      );
    }).toList();
  }
}
