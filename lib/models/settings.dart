class UserSettings {
  final String userDisplayName;
  final String lastNameFirst;

  const UserSettings({
    this.userDisplayName = '',
    this.lastNameFirst = '',
  });

  UserSettings copyWith({
    String? userDisplayName,
    String? lastNameFirst,
  }) {
    return UserSettings(
      userDisplayName: userDisplayName ?? this.userDisplayName,
      lastNameFirst: lastNameFirst ?? this.lastNameFirst,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'userDisplayName': userDisplayName,
      'lastNameFirst': lastNameFirst,
    };
  }

  factory UserSettings.fromMap(Map<String, dynamic> map) {
    return UserSettings(
      userDisplayName: map['userDisplayName'] as String? ?? '',
      lastNameFirst: map['lastNameFirst'] as String? ?? '',
    );
  }
}
