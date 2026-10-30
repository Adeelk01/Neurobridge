# NeuroBridge — Project Context Export

Auto-generated snapshot of folder structure and source files.

## Folder Structure

```
FlutterProjects/
  .firebaserc
  .flutter-plugins-dependencies
  .gitignore
  .metadata
  1.py
  README.md
  analysis_options.yaml
  firebase.json
  flutterprojects.iml
  project_context.md
  pubspec.lock
  pubspec.yaml
  functions/
    .gitignore
    index.js
    package.json
  lib/
    firebase_options.dart
    main.dart
    models/
    screens/
      admin/
        admin_home_screen.dart
        logs_screen.dart
        payments_screen.dart
        user_management_screen.dart
      auth/
        login_screen.dart
        signup_screen.dart
      chat/
        chat_screen.dart
      doctor/
        ai_summary_card.dart
        doctor_appointments_screen.dart
        doctor_home_screen.dart
        patient_records_screen.dart
      patient/
        book_appointment_screen.dart
        medical_records_screen.dart
        my_appointments_screen.dart
        patient_home_screen.dart
        questionnaire_screen.dart
    services/
      admin_service.dart
      auth_service.dart
      booking_service.dart
      chat_service.dart
      medical_record_service.dart
      questionnaire_service.dart
  test/
    widget_test.dart
```

## File Contents

### `.firebaserc`

```
{
  "projects": {
    "default": "neurobridge-ce999"
  }
}
```

### `analysis_options.yaml`

```yaml
# This file configures the analyzer, which statically analyzes Dart code to
# check for errors, warnings, and lints.
#
# The issues identified by the analyzer are surfaced in the UI of Dart-enabled
# IDEs (https://dart.dev/tools#ides-and-editors). The analyzer can also be
# invoked from the command line by running `flutter analyze`.

# The following line activates a set of recommended lints for Flutter apps,
# packages, and plugins designed to encourage good coding practices.
include: package:flutter_lints/flutter.yaml

linter:
  # The lint rules applied to this project can be customized in the
  # section below to disable rules from the `package:flutter_lints/flutter.yaml`
  # included above or to enable additional rules. A list of all available lints
  # and their documentation is published at https://dart.dev/lints.
  #
  # Instead of disabling a lint rule for the entire project in the
  # section below, it can also be suppressed for a single line of code
  # or a specific dart file by using the `// ignore: name_of_lint` and
  # `// ignore_for_file: name_of_lint` syntax on the line or in the file
  # producing the lint.
  rules:
    # avoid_print: false  # Uncomment to disable the `avoid_print` rule
    # prefer_single_quotes: true  # Uncomment to enable the `prefer_single_quotes` rule

# Additional information about this file can be found at
# https://dart.dev/guides/language/analysis-options
```

### `firebase.json`

```json
{
  "flutter": {
    "platforms": {
      "android": {
        "default": {
          "projectId": "neurobridge-ce999",
          "appId": "1:388082496297:android:9be2f85f54523bf484bd38",
          "fileOutput": "android/app/google-services.json"
        }
      },
      "dart": {
        "lib/firebase_options.dart": {
          "projectId": "neurobridge-ce999",
          "configurations": {
            "android": "1:388082496297:android:9be2f85f54523bf484bd38",
            "ios": "1:388082496297:ios:ca19cd13f50550b984bd38"
          }
        }
      }
    }
  },
  "functions": [
    {
      "source": "functions",
      "codebase": "default",
      "disallowLegacyRuntimeConfig": true,
      "ignore": [
        "node_modules",
        ".git",
        "firebase-debug.log",
        "firebase-debug.*.log",
        "*.local"
      ]
    }
  ]
}
```

### `pubspec.yaml`

```yaml
name: flutterprojects
description: "A new Flutter project."
publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: ^3.12.2

dependencies:
  flutter:
    sdk: flutter

  firebase_core: ^3.6.0
  firebase_auth: ^5.3.1
  cloud_firestore: ^5.4.3


  cupertino_icons: ^1.0.8
  http: ^1.2.0

dev_dependencies:
  flutter_test:
    sdk: flutter

  flutter_lints: ^6.0.0

flutter:
  uses-material-design: true
```

### `functions/index.js`

```javascript
/**
 * NeuroBridge — AI Questionnaire Cloud Functions
 * ------------------------------------------------
 * Two callable functions:
 *   1. generateQuestionnaireQuestions  -> patient submits chief complaint,
 *      Groq (Llama 3.3 70B) returns dynamic follow-up questions.
 *   2. analyzeQuestionnaireResponses   -> patient's answers are sent to
 *      Groq, which returns a clinical-style summary. Result is saved to
 *      Firestore's `questionnaireResponses` collection (FR-P-05 / FR-D-02).
 *
 * SETUP:
 *   1. Get a free API key from https://console.groq.com/keys (no card needed)
 *   2. In your functions folder run:
 *        firebase functions:secrets:set GROQ_API_KEY
 *      (paste the key when prompted)
 *   3. Deploy: firebase deploy --only functions
 *
 * package.json needs: "firebase-functions": "^5", "firebase-admin": "^12"
 * Node 18+ has global fetch(), so no extra HTTP library is required.
 */

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");

if (admin.apps.length === 0) {
  admin.initializeApp();
}

const GROQ_API_KEY = defineSecret("GROQ_API_KEY");
const GROQ_MODEL = "openai/gpt-oss-120b"; // free-tier, good JSON mode support
const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";

async function callGroq(apiKey, prompt, { json = false } = {}) {
  const body = {
    model: GROQ_MODEL,
    messages: [{ role: "user", content: prompt }],
    temperature: 0.4,
    ...(json ? { response_format: { type: "json_object" } } : {}),
  };

  const resp = await fetch(GROQ_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const errText = await resp.text();
    console.error("Groq API error:", resp.status, errText);
    throw new HttpsError("internal", "The AI service failed to respond.");
  }

  const data = await resp.json();
  const text = data?.choices?.[0]?.message?.content;
  if (!text) {
    throw new HttpsError("internal", "The AI service returned an empty response.");
  }
  return text;
}

/**
 * Callable: generateQuestionnaireQuestions
 * data: { chiefComplaint: string }
 * returns: { questions: [{ id, text, type }] }
 */
exports.generateQuestionnaireQuestions = onCall(
  { secrets: [GROQ_API_KEY] },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "You must be logged in.");
    }

    const chiefComplaint = (request.data?.chiefComplaint || "").trim();
    if (!chiefComplaint) {
      throw new HttpsError("invalid-argument", "chiefComplaint is required.");
    }
    if (chiefComplaint.length > 500) {
      throw new HttpsError("invalid-argument", "chiefComplaint is too long.");
    }

    const prompt = `You are a medical intake assistant helping prepare a patient for a doctor's appointment.
Patient's chief complaint: "${chiefComplaint}"

Generate 6 to 8 short, relevant pre-appointment screening questions a doctor
would want answered before seeing this patient. Do NOT attempt to diagnose or
suggest treatment — only ask clarifying intake questions (duration, severity,
triggers, associated symptoms, relevant history, etc).

Return ONLY valid JSON (no markdown fences, no extra text) matching exactly:
{"questions":[{"id":"q1","text":"...","type":"text"}]}

"type" must be one of: "text", "yes_no", "scale_1_10".`;

    const raw = await callGroq(GROQ_API_KEY.value(), prompt, { json: true });

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (e) {
      console.error("Failed to parse Groq JSON:", raw);
      throw new HttpsError("internal", "The AI returned an unexpected format.");
    }

    const questions = Array.isArray(parsed.questions) ? parsed.questions : [];
    if (questions.length === 0) {
      throw new HttpsError("internal", "The AI did not return any questions.");
    }

    return { questions };
  }
);

/**
 * Callable: analyzeQuestionnaireResponses
 * data: { chiefComplaint: string, answers: [{ question: string, answer: string }] }
 * returns: { responseId, analysisSummary }
 * Also writes a document to `questionnaireResponses` in Firestore.
 */
exports.analyzeQuestionnaireResponses = onCall(
  { secrets: [GROQ_API_KEY] },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "You must be logged in.");
    }

    const chiefComplaint = (request.data?.chiefComplaint || "").trim();
    const answers = request.data?.answers;

    if (!chiefComplaint || !Array.isArray(answers) || answers.length === 0) {
      throw new HttpsError(
        "invalid-argument",
        "chiefComplaint and a non-empty answers array are required."
      );
    }

    const qaText = answers
      .map((a, i) => `${i + 1}. ${a.question}\n   Answer: ${a.answer}`)
      .join("\n");

    const prompt = `You are assisting a doctor by summarizing a patient's pre-appointment
questionnaire. Chief complaint: "${chiefComplaint}"

Patient answers:
${qaText}

Write a concise clinical-style summary (max 150 words) covering key symptoms,
duration/severity if mentioned, and any notable red flags the doctor should
know before the appointment. Do NOT diagnose or recommend treatment — only
summarize what the patient reported. Return plain text, no markdown.`;

    const summary = (await callGroq(GROQ_API_KEY.value(), prompt)).trim();

    const db = admin.firestore();
    const docRef = await db.collection("questionnaireResponses").add({
      patientId: request.auth.uid,
      chiefComplaint,
      answers,
      analysisSummary: summary,
      analyzedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    return { responseId: docRef.id, analysisSummary: summary };
  }
);
```

### `functions/package.json`

```json
{
  "name": "functions",
  "description": "NeuroBridge Cloud Functions (AI Questionnaire)",
  "engines": {
    "node": "20"
  },
  "main": "index.js",
  "dependencies": {
    "firebase-admin": "^12.6.0",
    "firebase-functions": "^5.1.0"
  },
  "devDependencies": {
    "firebase-functions-test": "^3.1.0"
  },
  "private": true
}
```

### `lib/firebase_options.dart`

```dart
// File generated by FlutterFire CLI.
// ignore_for_file: type=lint
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      throw UnsupportedError(
        'DefaultFirebaseOptions have not been configured for web - '
        'you can reconfigure this by running the FlutterFire CLI again.',
      );
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for macos - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.windows:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for windows - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBp2eaHgIXutoTB2D9ZHh3i7nfdYDUzW8o',
    appId: '1:388082496297:android:9be2f85f54523bf484bd38',
    messagingSenderId: '388082496297',
    projectId: 'neurobridge-ce999',
    storageBucket: 'neurobridge-ce999.firebasestorage.app',
  );
  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyC_DMuG3R3ceA80AqR0lrC-uvztVffjU0w',
    appId: '1:388082496297:ios:ca19cd13f50550b984bd38',
    messagingSenderId: '388082496297',
    projectId: 'neurobridge-ce999',
    storageBucket: 'neurobridge-ce999.firebasestorage.app',
    iosClientId: '388082496297-5o3pl78esbuo1isv6l44i0r5r104e72j.apps.googleusercontent.com',
    iosBundleId: 'com.example.flutterprojects',
  );
}
```

### `lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'screens/auth/login_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(const NeuroBridgeApp());
}

class NeuroBridgeApp extends StatelessWidget {
  const NeuroBridgeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NeuroBridge',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.teal,
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}
```

### `lib/screens/admin/admin_home_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../auth/login_screen.dart';
import 'user_management_screen.dart';
import 'payments_screen.dart';
import 'logs_screen.dart';

class AdminHomeScreen extends StatelessWidget {
  const AdminHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().signOut();
              if (context.mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 12),
            const Text('Welcome, Admin!', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.people),
              label: const Text('Manage Users'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              onPressed: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const UserManagementScreen()));
              },
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.payments),
              label: const Text('Manage Payments'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              onPressed: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const PaymentsScreen()));
              },
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.history),
              label: const Text('View Logs'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              onPressed: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const LogsScreen()));
              },
            ),
          ],
        ),
      ),
    );
  }
}
```

### `lib/screens/admin/logs_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/admin_service.dart';

class LogsScreen extends StatelessWidget {
  const LogsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final AdminService adminService = AdminService();

    return Scaffold(
      appBar: AppBar(title: const Text('Activity Logs')),
      body: StreamBuilder<QuerySnapshot>(
        stream: adminService.getLogs(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No log entries yet.'));
          }

          final logs = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: logs.length,
            itemBuilder: (context, index) {
              final data = logs[index].data() as Map<String, dynamic>;
              return ListTile(
                leading: const Icon(Icons.history),
                title: Text('${data['action']} on ${data['entity']}'),
                subtitle: Text('Entity ID: ${data['entityId']}'),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/admin/payments_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/admin_service.dart';

class PaymentsScreen extends StatelessWidget {
  const PaymentsScreen({super.key});

  void _addPaymentDialog(BuildContext context) {
    final bookingIdController = TextEditingController();
    final amountController = TextEditingController();
    final adminService = AdminService();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Payment Record'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: bookingIdController,
              decoration: const InputDecoration(labelText: 'Booking ID'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: amountController,
              decoration: const InputDecoration(labelText: 'Amount'),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final amount = double.tryParse(amountController.text.trim()) ?? 0;
              await adminService.addPayment(
                bookingId: bookingIdController.text.trim(),
                amount: amount,
                status: 'paid',
              );
              if (context.mounted) Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final AdminService adminService = AdminService();

    return Scaffold(
      appBar: AppBar(title: const Text('Manage Payments')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _addPaymentDialog(context),
        child: const Icon(Icons.add),
      ),
      body: StreamBuilder<QuerySnapshot>(
        stream: adminService.getAllPayments(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No payments yet. Tap + to add one.'));
          }

          final payments = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: payments.length,
            itemBuilder: (context, index) {
              final doc = payments[index];
              final data = doc.data() as Map<String, dynamic>;
              final status = data['status'] ?? 'paid';

              Color statusColor = Colors.green;
              if (status == 'refunded') statusColor = Colors.orange;
              if (status == 'failed') statusColor = Colors.red;

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: Icon(Icons.receipt_long, color: statusColor),
                  title: Text('${data['amount']} ${data['currency'] ?? 'PKR'}'),
                  subtitle: Text('Booking: ${data['bookingId']} • $status'),
                  trailing: PopupMenuButton<String>(
                    onSelected: (value) => adminService.updatePaymentStatus(doc.id, value),
                    itemBuilder: (context) => const [
                      PopupMenuItem(value: 'paid', child: Text('Mark Paid')),
                      PopupMenuItem(value: 'refunded', child: Text('Mark Refunded')),
                      PopupMenuItem(value: 'failed', child: Text('Mark Failed')),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/admin/user_management_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/admin_service.dart';
import '../../services/auth_service.dart';

class UserManagementScreen extends StatelessWidget {
  const UserManagementScreen({super.key});

  void _editUserDialog(BuildContext context, String userId, Map<String, dynamic> data) {
    final nameController = TextEditingController(text: data['name']);
    String selectedRole = data['role'] ?? 'patient';
    final adminService = AdminService();

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Edit User'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Name'),
              ),
              const SizedBox(height: 12),
              DropdownButton<String>(
                value: selectedRole,
                isExpanded: true,
                items: const [
                  DropdownMenuItem(value: 'patient', child: Text('Patient')),
                  DropdownMenuItem(value: 'doctor', child: Text('Doctor')),
                  DropdownMenuItem(value: 'admin', child: Text('Admin')),
                ],
                onChanged: (value) => setDialogState(() => selectedRole = value!),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () async {
                await adminService.updateUser(userId, {
                  'name': nameController.text.trim(),
                  'role': selectedRole,
                });
                await adminService.writeLog(
                  entity: 'user',
                  entityId: userId,
                  action: 'update',
                  performedBy: AuthService().currentUser!.uid,
                );
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(BuildContext context, String userId) {
    final adminService = AdminService();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete User?'),
        content: const Text('This will remove the user\'s profile data. This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              await adminService.deleteUser(userId);
              await adminService.writeLog(
                entity: 'user',
                entityId: userId,
                action: 'delete',
                performedBy: AuthService().currentUser!.uid,
              );
              if (context.mounted) Navigator.pop(context);
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final AdminService adminService = AdminService();

    return Scaffold(
      appBar: AppBar(title: const Text('Manage Users')),
      body: StreamBuilder<QuerySnapshot>(
        stream: adminService.getAllUsers(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No users found.'));
          }

          final users = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: users.length,
            itemBuilder: (context, index) {
              final doc = users[index];
              final data = doc.data() as Map<String, dynamic>;
              final role = data['role'] ?? 'unknown';

              Color roleColor = Colors.blue;
              if (role == 'doctor') roleColor = Colors.teal;
              if (role == 'admin') roleColor = Colors.purple;

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: CircleAvatar(backgroundColor: roleColor, child: const Icon(Icons.person, color: Colors.white)),
                  title: Text(data['name'] ?? 'Unnamed'),
                  subtitle: Text('${data['email'] ?? ''} • $role'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit, color: Colors.blue),
                        onPressed: () => _editUserDialog(context, doc.id, data),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () => _confirmDelete(context, doc.id),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/auth/login_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'signup_screen.dart';
import '../patient/patient_home_screen.dart';
import '../doctor/doctor_home_screen.dart';
import '../admin/admin_home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final AuthService _authService = AuthService();

  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final error = await _authService.logIn(
      email: _emailController.text.trim(),
      password: _passwordController.text.trim(),
    );

    if (error != null) {
      setState(() {
        _isLoading = false;
        _errorMessage = error;
      });
      return;
    }

    // Login successful — check the user's role and navigate accordingly
    final uid = _authService.currentUser!.uid;
    final role = await _authService.getUserRole(uid);

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (role == 'patient') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const PatientHomeScreen()),
      );
    } else if (role == 'doctor') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const DoctorHomeScreen()),
      );
    } else if (role == 'admin') {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const AdminHomeScreen()),
      );
    } else {
      setState(() => _errorMessage = 'Unknown user role. Contact support.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.health_and_safety, size: 72, color: Colors.teal),
                const SizedBox(height: 16),
                const Text(
                  'NeuroBridge',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 40),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) return 'Enter your email';
                    if (!value.contains('@')) return 'Enter a valid email';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.length < 6) {
                      return 'Password must be at least 6 characters';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                if (_errorMessage != null)
                  Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.red),
                  ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: _isLoading
                      ? const SizedBox(
                    height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                      : const Text('Log In'),
                ),
                const SizedBox(height: 12),
                TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SignupScreen()),
                    );
                  },
                  child: const Text("Don't have an account? Sign up"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

### `lib/screens/auth/signup_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final AuthService _authService = AuthService();

  String _selectedRole = 'patient'; // default
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _handleSignup() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final error = await _authService.signUp(
      name: _nameController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text.trim(),
      role: _selectedRole,
    );

    setState(() => _isLoading = false);

    if (error != null) {
      setState(() => _errorMessage = error);
      return;
    }

    // Signup successful — go back to login screen so they can log in
    if (!mounted) return;
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Account created! Please log in.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Full Name',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) return 'Enter your name';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) return 'Enter your email';
                    if (!value.contains('@')) return 'Enter a valid email';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Password',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.length < 6) {
                      return 'Password must be at least 6 characters';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),
                const Text('I am a:', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: RadioListTile<String>(
                        title: const Text('Patient'),
                        value: 'patient',
                        groupValue: _selectedRole,
                        onChanged: (value) => setState(() => _selectedRole = value!),
                      ),
                    ),
                    Expanded(
                      child: RadioListTile<String>(
                        title: const Text('Doctor'),
                        value: 'doctor',
                        groupValue: _selectedRole,
                        onChanged: (value) => setState(() => _selectedRole = value!),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                if (_errorMessage != null)
                  Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.red),
                  ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleSignup,
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: _isLoading
                      ? const SizedBox(
                    height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                      : const Text('Sign Up'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

### `lib/screens/chat/chat_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/chat_service.dart';

class ChatScreen extends StatefulWidget {
  final String otherUserId;
  final String otherUserName;

  const ChatScreen({
    super.key,
    required this.otherUserId,
    required this.otherUserName,
  });

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ChatService _chatService = ChatService();
  final TextEditingController _messageController = TextEditingController();
  late final String _myId;

  @override
  void initState() {
    super.initState();
    _myId = AuthService().currentUser!.uid;
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _chatService.sendMessage(
      senderId: _myId,
      receiverId: widget.otherUserId,
      content: text,
    );
    _messageController.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.otherUserName)),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: _chatService.getMessages(_myId, widget.otherUserId),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                  return const Center(child: Text('Say hello 👋'));
                }

                final messages = snapshot.data!.docs;

                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final data = messages[index].data() as Map<String, dynamic>;
                    final isMe = data['senderId'] == _myId;

                    return Align(
                      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.7,
                        ),
                        decoration: BoxDecoration(
                          color: isMe ? Colors.teal : Colors.grey[300],
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Text(
                          data['content'] ?? '',
                          style: TextStyle(color: isMe ? Colors.white : Colors.black87),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      decoration: InputDecoration(
                        hintText: 'Type a message...',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: Colors.teal,
                    child: IconButton(
                      icon: const Icon(Icons.send, color: Colors.white),
                      onPressed: _sendMessage,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

### `lib/screens/doctor/ai_summary_card.dart`

```dart
// lib/screens/doctor/ai_summary_card.dart
//
// FR-D-02: Doctor views the AI-generated summary of a patient's
// questionnaire. Drop this into the patient profile screen on the
// doctor side. Firestore security rules (separate task) should ensure
// only the assigned doctor can read a given patient's responses.

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

class AiSummaryCard extends StatelessWidget {
  final String patientId;

  const AiSummaryCard({super.key, required this.patientId});

  @override
  Widget build(BuildContext context) {
    final query = FirebaseFirestore.instance
        .collection('questionnaireResponses')
        .where('patientId', isEqualTo: patientId)
        .orderBy('analyzedAt', descending: true)
        .limit(1);

    return StreamBuilder<QuerySnapshot>(
      stream: query.snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.all(16),
            child: Center(child: CircularProgressIndicator()),
          );
        }
        if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
          return const Padding(
            padding: EdgeInsets.all(16),
            child: Text('No questionnaire submitted yet.'),
          );
        }

        final doc = snapshot.data!.docs.first;
        final data = doc.data() as Map<String, dynamic>;
        final complaint = data['chiefComplaint'] ?? '';
        final summary = data['analysisSummary'] ?? '';

        return Card(
          margin: const EdgeInsets.all(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    Icon(Icons.smart_toy_outlined, size: 20),
                    SizedBox(width: 8),
                    Text('AI Pre-Appointment Summary',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Chief complaint: $complaint',
                    style: const TextStyle(fontStyle: FontStyle.italic)),
                const SizedBox(height: 8),
                Text(summary),
              ],
            ),
          ),
        );
      },
    );
  }
}
```

### `lib/screens/doctor/doctor_appointments_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/booking_service.dart';
import '../chat/chat_screen.dart';
import 'patient_records_screen.dart';

class DoctorAppointmentsScreen extends StatelessWidget {
  const DoctorAppointmentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final BookingService bookingService = BookingService();
    final doctorId = AuthService().currentUser!.uid;

    return Scaffold(
      appBar: AppBar(title: const Text('Appointment Requests')),
      body: StreamBuilder<QuerySnapshot>(
        stream: bookingService.getDoctorBookings(doctorId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No appointments yet.'));
          }

          final bookings = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: bookings.length,
            itemBuilder: (context, index) {
              final doc = bookings[index];
              final data = doc.data() as Map<String, dynamic>;
              final dateTime = (data['dateTime'] as Timestamp).toDate();
              final status = data['status'] ?? 'pending';
              final patientId = data['patientId'] ?? '';

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Fetch patient name
                      FutureBuilder<DocumentSnapshot>(
                        future: FirebaseFirestore.instance
                            .collection('users')
                            .doc(patientId)
                            .get(),
                        builder: (context, patientSnapshot) {
                          String patientName = 'Loading...';
                          if (patientSnapshot.hasData && patientSnapshot.data!.exists) {
                            final pData = patientSnapshot.data!.data() as Map<String, dynamic>;
                            patientName = pData['name'] ?? 'Unknown Patient';
                          }
                          return Text(
                            patientName,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          );
                        },
                      ),
                      const SizedBox(height: 4),
                      Text('${dateTime.day}/${dateTime.month}/${dateTime.year} at ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}'),
                      const SizedBox(height: 4),
                      Text('Status: $status',
                          style: TextStyle(
                            color: status == 'confirmed'
                                ? Colors.green
                                : status == 'cancelled'
                                ? Colors.red
                                : Colors.orange,
                            fontWeight: FontWeight.bold,
                          )),
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.chat_bubble_outline),
                        label: const Text('Message Patient'),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ChatScreen(
                                otherUserId: patientId,
                                otherUserName: 'Patient',
                              ),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 4),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.folder_shared),
                        label: const Text('View/Add Records'),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => PatientRecordsScreen(
                                patientId: patientId,
                                patientName: 'Patient',
                              ),
                            ),
                          );
                        },
                      ),
                      if (status == 'pending') ...[
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                              onPressed: () => bookingService.updateBookingStatus(doc.id, 'confirmed'),
                              child: const Text('Accept'),
                            ),
                            const SizedBox(width: 8),
                            OutlinedButton(
                              onPressed: () => bookingService.updateBookingStatus(doc.id, 'cancelled'),
                              child: const Text('Reject'),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/doctor/doctor_home_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../auth/login_screen.dart';
import 'doctor_appointments_screen.dart';

class DoctorHomeScreen extends StatelessWidget {
  const DoctorHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Doctor Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().signOut();
              if (context.mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 20),
            const Text(
              'Welcome, Doctor!',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.calendar_month),
              label: const Text('View Appointment Requests'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const DoctorAppointmentsScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
```

### `lib/screens/doctor/patient_records_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/medical_record_service.dart';
import 'ai_summary_card.dart';

class PatientRecordsScreen extends StatelessWidget {
  final String patientId;
  final String patientName;

  const PatientRecordsScreen({
    super.key,
    required this.patientId,
    required this.patientName,
  });

  void _showAddRecordDialog(BuildContext context) {
    final titleController = TextEditingController();
    final descriptionController = TextEditingController();
    final recordService = MedicalRecordService();
    final doctorId = AuthService().currentUser!.uid;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Medical Record'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleController,
              decoration: const InputDecoration(labelText: 'Title (e.g. Diagnosis)'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: descriptionController,
              decoration: const InputDecoration(labelText: 'Description / Notes'),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (titleController.text.trim().isEmpty) return;
              await recordService.addRecord(
                patientId: patientId,
                doctorId: doctorId,
                title: titleController.text.trim(),
                description: descriptionController.text.trim(),
              );
              if (context.mounted) Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final MedicalRecordService recordService = MedicalRecordService();

    return Scaffold(
      appBar: AppBar(title: Text('$patientName\'s Records')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddRecordDialog(context),
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          // FR-D-02: AI-generated summary of the patient's latest
          // pre-appointment questionnaire.
          AiSummaryCard(patientId: patientId),
          const Divider(height: 1),
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: recordService.getPatientRecords(patientId),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                  return const Center(child: Text('No records yet. Tap + to add one.'));
                }

                final records = snapshot.data!.docs;

                return ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: records.length,
                  itemBuilder: (context, index) {
                    final data = records[index].data() as Map<String, dynamic>;
                    final createdAt = data['createdAt'] as Timestamp?;
                    final dateStr = createdAt != null
                        ? '${createdAt.toDate().day}/${createdAt.toDate().month}/${createdAt.toDate().year}'
                        : '';

                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      child: ListTile(
                        leading: const Icon(Icons.description, color: Colors.teal),
                        title: Text(data['title'] ?? 'Untitled'),
                        subtitle: Text(data['description'] ?? ''),
                        trailing: Text(dateStr, style: const TextStyle(fontSize: 12)),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
```

### `lib/screens/patient/book_appointment_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/booking_service.dart';
import '../../services/auth_service.dart';

class BookAppointmentScreen extends StatefulWidget {
  final String doctorId;
  final String doctorName;

  const BookAppointmentScreen({
    super.key,
    required this.doctorId,
    required this.doctorName,
  });

  @override
  State<BookAppointmentScreen> createState() => _BookAppointmentScreenState();
}

class _BookAppointmentScreenState extends State<BookAppointmentScreen> {
  final BookingService _bookingService = BookingService();
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  bool _isLoading = false;

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 60)),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 10, minute: 0),
    );
    if (picked != null) setState(() => _selectedTime = picked);
  }

  Future<void> _confirmBooking() async {
    if (_selectedDate == null || _selectedTime == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a date and time')),
      );
      return;
    }

    setState(() => _isLoading = true);

    final dateTime = DateTime(
      _selectedDate!.year,
      _selectedDate!.month,
      _selectedDate!.day,
      _selectedTime!.hour,
      _selectedTime!.minute,
    );

    final patientId = AuthService().currentUser!.uid;
    final error = await _bookingService.bookAppointment(
      patientId: patientId,
      doctorId: widget.doctorId,
      dateTime: dateTime,
    );

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (error == null) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Appointment request sent!')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $error')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Book with Dr. ${widget.doctorName}')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ListTile(
              leading: const Icon(Icons.calendar_today),
              title: Text(_selectedDate == null
                  ? 'Select Date'
                  : '${_selectedDate!.day}/${_selectedDate!.month}/${_selectedDate!.year}'),
              tileColor: Colors.grey[200],
              onTap: _pickDate,
            ),
            const SizedBox(height: 12),
            ListTile(
              leading: const Icon(Icons.access_time),
              title: Text(_selectedTime == null
                  ? 'Select Time'
                  : _selectedTime!.format(context)),
              tileColor: Colors.grey[200],
              onTap: _pickTime,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _isLoading ? null : _confirmBooking,
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              child: _isLoading
                  ? const SizedBox(
                height: 20, width: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
              )
                  : const Text('Confirm Appointment'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### `lib/screens/patient/medical_records_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/medical_record_service.dart';

class MedicalRecordsScreen extends StatelessWidget {
  const MedicalRecordsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final MedicalRecordService recordService = MedicalRecordService();
    final patientId = AuthService().currentUser!.uid;

    return Scaffold(
      appBar: AppBar(title: const Text('My Medical Records')),
      body: StreamBuilder<QuerySnapshot>(
        stream: recordService.getPatientRecords(patientId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No medical records yet.'));
          }

          final records = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: records.length,
            itemBuilder: (context, index) {
              final data = records[index].data() as Map<String, dynamic>;
              final createdAt = data['createdAt'] as Timestamp?;
              final dateStr = createdAt != null
                  ? '${createdAt.toDate().day}/${createdAt.toDate().month}/${createdAt.toDate().year}'
                  : '';

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: const Icon(Icons.description, color: Colors.teal),
                  title: Text(data['title'] ?? 'Untitled'),
                  subtitle: Text(data['description'] ?? ''),
                  trailing: Text(dateStr, style: const TextStyle(fontSize: 12)),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/patient/my_appointments_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/booking_service.dart';

class MyAppointmentsScreen extends StatelessWidget {
  const MyAppointmentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final BookingService bookingService = BookingService();
    final patientId = AuthService().currentUser!.uid;

    return Scaffold(
      appBar: AppBar(title: const Text('My Appointments')),
      body: StreamBuilder<QuerySnapshot>(
        stream: bookingService.getPatientBookings(patientId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No appointments yet.'));
          }

          final bookings = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: bookings.length,
            itemBuilder: (context, index) {
              final doc = bookings[index];
              final data = doc.data() as Map<String, dynamic>;
              final dateTime = (data['dateTime'] as Timestamp).toDate();
              final status = data['status'] ?? 'pending';

              Color statusColor = Colors.orange;
              if (status == 'confirmed') statusColor = Colors.green;
              if (status == 'cancelled') statusColor = Colors.red;

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: Icon(Icons.event, color: statusColor),
                  title: Text('${dateTime.day}/${dateTime.month}/${dateTime.year} at ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}'),
                  subtitle: Text('Status: $status'),
                  trailing: status == 'pending' || status == 'confirmed'
                      ? IconButton(
                    icon: const Icon(Icons.cancel, color: Colors.red),
                    tooltip: 'Cancel',
                    onPressed: () => bookingService.cancelBooking(doc.id),
                  )
                      : null,
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/patient/patient_home_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../services/auth_service.dart';
import '../../services/booking_service.dart';
import '../auth/login_screen.dart';
import '../chat/chat_screen.dart';
import 'book_appointment_screen.dart';
import 'my_appointments_screen.dart';
import 'medical_records_screen.dart';
import 'questionnaire_screen.dart';

class PatientHomeScreen extends StatelessWidget {
  const PatientHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final BookingService bookingService = BookingService();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Find a Doctor'),
        actions: [
          IconButton(
            icon: const Icon(Icons.assignment_outlined),
            tooltip: 'Pre-Appointment Questionnaire',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const QuestionnaireScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.folder_shared),
            tooltip: 'My Medical Records',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MedicalRecordsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.calendar_month),
            tooltip: 'My Appointments',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MyAppointmentsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().signOut();
              if (context.mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: StreamBuilder<QuerySnapshot>(
        stream: bookingService.getDoctors(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
            return const Center(child: Text('No doctors available yet.'));
          }

          final doctors = snapshot.data!.docs;

          return ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: doctors.length,
            itemBuilder: (context, index) {
              final doc = doctors[index];
              final data = doc.data() as Map<String, dynamic>;
              final name = data['name'] ?? 'Unknown';

              return Card(
                margin: const EdgeInsets.symmetric(vertical: 6),
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.medical_services)),
                  title: Text('Dr. $name'),
                  subtitle: const Text('General Practitioner'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.chat_bubble_outline, color: Colors.teal),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ChatScreen(
                                otherUserId: doc.id,
                                otherUserName: 'Dr. $name',
                              ),
                            ),
                          );
                        },
                      ),
                      ElevatedButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => BookAppointmentScreen(
                                doctorId: doc.id,
                                doctorName: name,
                              ),
                            ),
                          );
                        },
                        child: const Text('Book'),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### `lib/screens/patient/questionnaire_screen.dart`

```dart
// lib/screens/patient/questionnaire_screen.dart
//
// FR-P-05: Patient fills a pre-appointment questionnaire; answers are
// analyzed by AI into a summary for the doctor.

import 'package:flutter/material.dart';
import '../../services/questionnaire_service.dart';

class QuestionnaireScreen extends StatefulWidget {
  const QuestionnaireScreen({super.key});

  @override
  State<QuestionnaireScreen> createState() => _QuestionnaireScreenState();
}

class _QuestionnaireScreenState extends State<QuestionnaireScreen> {
  final _service = QuestionnaireService();
  final _complaintController = TextEditingController();

  bool _loadingQuestions = false;
  bool _submitting = false;
  bool _submitted = false;

  List<Question> _questions = [];
  final Map<String, String> _answers = {};

  @override
  void dispose() {
    _complaintController.dispose();
    super.dispose();
  }

  Future<void> _generateQuestions() async {
    final complaint = _complaintController.text.trim();
    if (complaint.isEmpty) {
      _showError('Please describe your main symptom or reason for visit.');
      return;
    }
    setState(() => _loadingQuestions = true);
    try {
      final questions = await _service.generateQuestions(complaint);
      setState(() {
        _questions = questions;
        _loadingQuestions = false;
      });
    } on QuestionnaireException catch (e) {
      setState(() => _loadingQuestions = false);
      _showError(e.message);
    } catch (_) {
      setState(() => _loadingQuestions = false);
      _showError('Something went wrong. Please try again.');
    }
  }

  Future<void> _submit() async {
    if (_answers.length < _questions.length ||
        _answers.values.any((v) => v.trim().isEmpty)) {
      _showError('Please answer all questions before submitting.');
      return;
    }
    setState(() => _submitting = true);
    try {
      final answersList = _questions
          .map((q) => {'question': q.text, 'answer': _answers[q.id] ?? ''})
          .toList();
      await _service.submitAnswers(
        chiefComplaint: _complaintController.text.trim(),
        answers: answersList,
      );
      setState(() {
        _submitting = false;
        _submitted = true;
      });
    } on QuestionnaireException catch (e) {
      setState(() => _submitting = false);
      _showError(e.message);
    } catch (_) {
      setState(() => _submitting = false);
      _showError('Could not submit questionnaire. Please try again.');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Widget _buildQuestionInput(Question q) {
    switch (q.type) {
      case 'yes_no':
        return Row(
          children: [
            Expanded(
              child: RadioListTile<String>(
                contentPadding: EdgeInsets.zero,
                title: const Text('Yes'),
                value: 'Yes',
                groupValue: _answers[q.id],
                onChanged: (v) => setState(() => _answers[q.id] = v!),
              ),
            ),
            Expanded(
              child: RadioListTile<String>(
                contentPadding: EdgeInsets.zero,
                title: const Text('No'),
                value: 'No',
                groupValue: _answers[q.id],
                onChanged: (v) => setState(() => _answers[q.id] = v!),
              ),
            ),
          ],
        );
      case 'scale_1_10':
        final current = int.tryParse(_answers[q.id] ?? '') ?? 5;
        return Row(
          children: [
            Expanded(
              child: Slider(
                min: 1,
                max: 10,
                divisions: 9,
                value: current.toDouble(),
                label: current.toString(),
                onChanged: (v) =>
                    setState(() => _answers[q.id] = v.round().toString()),
              ),
            ),
            SizedBox(width: 24, child: Text('$current')),
          ],
        );
      default:
        return TextField(
          decoration: const InputDecoration(
            hintText: 'Your answer',
            border: OutlineInputBorder(),
          ),
          onChanged: (v) => setState(() => _answers[q.id] = v),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pre-Appointment Questionnaire')),
      body: _submitted ? _buildConfirmation() : _buildForm(),
    );
  }

  Widget _buildForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Briefly describe your main symptom or reason for visit:',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _complaintController,
            decoration: const InputDecoration(
              hintText: 'e.g. Persistent headache for 3 days',
              border: OutlineInputBorder(),
            ),
            maxLines: 2,
            enabled: _questions.isEmpty,
          ),
          const SizedBox(height: 12),
          if (_questions.isEmpty)
            ElevatedButton(
              onPressed: _loadingQuestions ? null : _generateQuestions,
              child: _loadingQuestions
                  ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
                  : const Text('Continue'),
            ),
          if (_questions.isNotEmpty) ...[
            const Divider(height: 32),
            ..._questions.map(
                  (q) => Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(q.text,
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    _buildQuestionInput(q),
                  ],
                ),
              ),
            ),
            ElevatedButton(
              onPressed: _submitting ? null : _submit,
              child: _submitting
                  ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
                  : const Text('Submit Questionnaire'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildConfirmation() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle, color: Colors.green, size: 64),
          const SizedBox(height: 16),
          const Text(
            'Thank you. Your responses have been sent to your doctor.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }
}
```

### `lib/services/admin_service.dart`

```dart
import 'package:cloud_firestore/cloud_firestore.dart';

class AdminService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Get all users (patients + doctors)
  Stream<QuerySnapshot> getAllUsers() {
    return _firestore.collection('users').orderBy('createdAt', descending: true).snapshots();
  }

  // Update a user's info
  Future<void> updateUser(String userId, Map<String, dynamic> data) async {
    await _firestore.collection('users').doc(userId).update(data);
  }

  // Delete a user's Firestore record
  // Note: this removes their profile data. Deleting the actual login
  // account requires Firebase Admin SDK (a backend), which is outside
  // this app's scope, but is fine to mention as a known limitation.
  Future<void> deleteUser(String userId) async {
    await _firestore.collection('users').doc(userId).delete();
  }

  // Get all payments
  Stream<QuerySnapshot> getAllPayments() {
    return _firestore.collection('payments').orderBy('processedAt', descending: true).snapshots();
  }

  // Add a payment record
  Future<void> addPayment({
    required String bookingId,
    required double amount,
    required String status,
  }) async {
    await _firestore.collection('payments').add({
      'bookingId': bookingId,
      'amount': amount,
      'currency': 'PKR',
      'status': status,
      'processedAt': FieldValue.serverTimestamp(),
    });
  }

  // Update payment status (confirm / refund)
  Future<void> updatePaymentStatus(String paymentId, String status) async {
    await _firestore.collection('payments').doc(paymentId).update({'status': status});
  }

  // Simple log entry writer, used across admin actions
  Future<void> writeLog({
    required String entity,
    required String entityId,
    required String action,
    required String performedBy,
  }) async {
    await _firestore.collection('logs').add({
      'entity': entity,
      'entityId': entityId,
      'action': action,
      'performedBy': performedBy,
      'timestamp': FieldValue.serverTimestamp(),
    });
  }

  // Get logs
  Stream<QuerySnapshot> getLogs() {
    return _firestore.collection('logs').orderBy('timestamp', descending: true).snapshots();
  }
}
```

### `lib/services/auth_service.dart`

```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Current logged-in user
  User? get currentUser => _auth.currentUser;

  // Sign up a new user (patient or doctor)
  Future<String?> signUp({
    required String name,
    required String email,
    required String password,
    required String role, // "patient" or "doctor"
  }) async {
    try {
      UserCredential result = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      // Save extra user info in Firestore
      await _firestore.collection('users').doc(result.user!.uid).set({
        'userId': result.user!.uid,
        'name': name,
        'email': email,
        'role': role,
        'createdAt': FieldValue.serverTimestamp(),
      });

      return null; // null means success
    } on FirebaseAuthException catch (e) {
      return e.message ?? 'Signup failed';
    }
  }

  // Log in existing user
  Future<String?> logIn({
    required String email,
    required String password,
  }) async {
    try {
      await _auth.signInWithEmailAndPassword(email: email, password: password);
      return null; // success
    } on FirebaseAuthException catch (e) {
      return e.message ?? 'Login failed';
    }
  }

  // Get the role of the currently logged-in user
  Future<String?> getUserRole(String uid) async {
    DocumentSnapshot doc = await _firestore.collection('users').doc(uid).get();
    if (doc.exists) {
      return doc.get('role') as String;
    }
    return null;
  }

  // Log out
  Future<void> signOut() async {
    await _auth.signOut();
  }
}
```

### `lib/services/booking_service.dart`

```dart
import 'package:cloud_firestore/cloud_firestore.dart';

class BookingService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Get all doctors
  Stream<QuerySnapshot> getDoctors() {
    return _firestore
        .collection('users')
        .where('role', isEqualTo: 'doctor')
        .snapshots();
  }

  // Book an appointment
  Future<String?> bookAppointment({
    required String patientId,
    required String doctorId,
    required DateTime dateTime,
  }) async {
    try {
      await _firestore.collection('bookings').add({
        'patientId': patientId,
        'doctorId': doctorId,
        'dateTime': Timestamp.fromDate(dateTime),
        'status': 'pending',
        'createdAt': FieldValue.serverTimestamp(),
      });
      return null; // success
    } catch (e) {
      return e.toString();
    }
  }

  // Get bookings for a patient
  Stream<QuerySnapshot> getPatientBookings(String patientId) {
    return _firestore
        .collection('bookings')
        .where('patientId', isEqualTo: patientId)
        .orderBy('dateTime')
        .snapshots();
  }

  // Get bookings for a doctor
  Stream<QuerySnapshot> getDoctorBookings(String doctorId) {
    return _firestore
        .collection('bookings')
        .where('doctorId', isEqualTo: doctorId)
        .orderBy('dateTime')
        .snapshots();
  }

  // Cancel a booking
  Future<void> cancelBooking(String bookingId) async {
    await _firestore.collection('bookings').doc(bookingId).update({
      'status': 'cancelled',
    });
  }

  // Doctor accepts/rejects a booking
  Future<void> updateBookingStatus(String bookingId, String status) async {
    await _firestore.collection('bookings').doc(bookingId).update({
      'status': status,
    });
  }
}
```

### `lib/services/chat_service.dart`

```dart
import 'package:cloud_firestore/cloud_firestore.dart';

class ChatService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Creates a consistent, unique chat ID for any 2 users (order doesn't matter)
  String getChatId(String userId1, String userId2) {
    List<String> ids = [userId1, userId2];
    ids.sort();
    return ids.join('_');
  }

  // Send a message
  Future<void> sendMessage({
    required String senderId,
    required String receiverId,
    required String content,
  }) async {
    final chatId = getChatId(senderId, receiverId);

    await _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .add({
      'senderId': senderId,
      'receiverId': receiverId,
      'content': content,
      'sentAt': FieldValue.serverTimestamp(),
    });

    // Also save a summary doc so we can list conversations later
    await _firestore.collection('chats').doc(chatId).set({
      'participants': [senderId, receiverId],
      'lastMessage': content,
      'lastMessageAt': FieldValue.serverTimestamp(),
    }, SetOptions(merge: true));
  }

  // Stream of messages between two users, oldest to newest
  Stream<QuerySnapshot> getMessages(String userId1, String userId2) {
    final chatId = getChatId(userId1, userId2);
    return _firestore
        .collection('chats')
        .doc(chatId)
        .collection('messages')
        .orderBy('sentAt', descending: false)
        .snapshots();
  }
}
```

### `lib/services/medical_record_service.dart`

```dart
import 'package:cloud_firestore/cloud_firestore.dart';

class MedicalRecordService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Doctor adds a new medical record for a patient
  Future<void> addRecord({
    required String patientId,
    required String doctorId,
    required String title,
    required String description,
  }) async {
    await _firestore.collection('medicalRecords').add({
      'patientId': patientId,
      'doctorId': doctorId,
      'title': title,
      'description': description,
      'createdAt': FieldValue.serverTimestamp(),
    });
  }

  // Get all records for a patient (used by both patient view and doctor view)
  Stream<QuerySnapshot> getPatientRecords(String patientId) {
    return _firestore
        .collection('medicalRecords')
        .where('patientId', isEqualTo: patientId)
        .orderBy('createdAt', descending: true)
        .snapshots();
  }
}
```

### `lib/services/questionnaire_service.dart`

```dart
// lib/services/questionnaire_service.dart
//
// Calls Groq's API directly from the Flutter app (no Firebase Cloud
// Functions / Blaze plan required). Meant for FYP/demo use.
//
// ⚠️ SECURITY NOTE: The Groq API key below is embedded in the client and
// can be extracted by anyone who decompiles the app. This is acceptable
// for a student project demo, but NOT recommended for production apps.
// To reduce risk:
//   - Set a low rate limit / spend cap on this key in the Groq dashboard
//     (console.groq.com/settings/limits)
//   - Rotate the key before public release or after submission
//   - Never commit the key to a public GitHub repo (use --dart-define,
//     see notes at the bottom of this file)

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class Question {
  final String id;
  final String text;
  final String type; // "text" | "yes_no" | "scale_1_10"

  Question({required this.id, required this.text, required this.type});

  factory Question.fromMap(Map<String, dynamic> map) {
    return Question(
      id: map['id']?.toString() ?? '',
      text: map['text']?.toString() ?? '',
      type: map['type']?.toString() ?? 'text',
    );
  }
}

class QuestionnaireException implements Exception {
  final String message;
  QuestionnaireException(this.message);
  @override
  String toString() => message;
}

class QuestionnaireService {
  // TODO: paste your Groq key here, or better, pass it via
  // --dart-define=GROQ_API_KEY=xxxx (see bottom of file).
  static const String _groqApiKey = String.fromEnvironment(
    'GROQ_API_KEY',
    defaultValue: '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',
  );

  static const String _groqUrl =
      'https://api.groq.com/openai/v1/chat/completions';
  static const String _groqModel = 'openai/gpt-oss-120b';

  final FirebaseFirestore _firestore;
  final FirebaseAuth _auth;

  QuestionnaireService({
    FirebaseFirestore? firestore,
    FirebaseAuth? auth,
  })  : _firestore = firestore ?? FirebaseFirestore.instance,
        _auth = auth ?? FirebaseAuth.instance;

  Future<String> _callGroq(String prompt, {bool json = false}) async {
    if (_groqApiKey.isEmpty || _groqApiKey == 'PASTE_YOUR_GROQ_API_KEY_HERE') {
      throw QuestionnaireException(
        'Groq API key is not set. Add it in questionnaire_service.dart '
            'or pass --dart-define=GROQ_API_KEY=your_key when running.',
      );
    }

    final body = {
      'model': _groqModel,
      'messages': [
        {'role': 'user', 'content': prompt}
      ],
      'temperature': 0.4,
      if (json) 'response_format': {'type': 'json_object'},
    };

    http.Response resp;
    try {
      resp = await http.post(
        Uri.parse(_groqUrl),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_groqApiKey',
        },
        body: jsonEncode(body),
      );
    } catch (e) {
      throw QuestionnaireException('Could not reach the AI service: $e');
    }

    if (resp.statusCode != 200) {
      // ignore: avoid_print
      print('Groq API error: ${resp.statusCode} ${resp.body}');
      throw QuestionnaireException('The AI service failed to respond.');
    }

    final data = jsonDecode(resp.body);
    final text = data?['choices']?[0]?['message']?['content'] as String?;
    if (text == null || text.isEmpty) {
      throw QuestionnaireException('The AI service returned an empty response.');
    }
    return text;
  }

  /// Step 1: send the patient's chief complaint, get back AI-generated
  /// follow-up questions.
  Future<List<Question>> generateQuestions(String chiefComplaint) async {
    final complaint = chiefComplaint.trim();
    if (complaint.isEmpty) {
      throw QuestionnaireException('chiefComplaint is required.');
    }
    if (complaint.length > 500) {
      throw QuestionnaireException('chiefComplaint is too long.');
    }

    final prompt =
    '''You are a medical intake assistant helping prepare a patient for a doctor's appointment.
Patient's chief complaint: "$complaint"

Generate 6 to 8 short, relevant pre-appointment screening questions a doctor
would want answered before seeing this patient. Do NOT attempt to diagnose or
suggest treatment — only ask clarifying intake questions (duration, severity,
triggers, associated symptoms, relevant history, etc).

Return ONLY valid JSON (no markdown fences, no extra text) matching exactly:
{"questions":[{"id":"q1","text":"...","type":"text"}]}

"type" must be one of: "text", "yes_no", "scale_1_10".''';

    final raw = await _callGroq(prompt, json: true);

    Map<String, dynamic> parsed;
    try {
      parsed = jsonDecode(raw) as Map<String, dynamic>;
    } catch (e) {
      // ignore: avoid_print
      print('Failed to parse Groq JSON: $raw');
      throw QuestionnaireException('The AI returned an unexpected format.');
    }

    final rawQuestions = parsed['questions'];
    if (rawQuestions is! List || rawQuestions.isEmpty) {
      throw QuestionnaireException('The AI did not return any questions.');
    }

    return rawQuestions
        .map((q) => Question.fromMap(Map<String, dynamic>.from(q as Map)))
        .toList();
  }

  /// Step 2: send the patient's answers, get back the AI clinical summary,
  /// and save the record to Firestore (previously done server-side).
  Future<String> submitAnswers({
    required String chiefComplaint,
    required List<Map<String, String>> answers,
  }) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw QuestionnaireException('You must be logged in.');
    }

    final complaint = chiefComplaint.trim();
    if (complaint.isEmpty || answers.isEmpty) {
      throw QuestionnaireException(
        'chiefComplaint and a non-empty answers array are required.',
      );
    }

    final qaText = answers
        .asMap()
        .entries
        .map((e) =>
    '${e.key + 1}. ${e.value['question']}\n   Answer: ${e.value['answer']}')
        .join('\n');

    final prompt =
    '''You are assisting a doctor by summarizing a patient's pre-appointment
questionnaire. Chief complaint: "$complaint"

Patient answers:
$qaText

Write a concise clinical-style summary (max 150 words) covering key symptoms,
duration/severity if mentioned, and any notable red flags the doctor should
know before the appointment. Do NOT diagnose or recommend treatment — only
summarize what the patient reported. Return plain text, no markdown.''';

    final summary = (await _callGroq(prompt)).trim();

    final docRef = await _firestore.collection('questionnaireResponses').add({
      'patientId': user.uid,
      'chiefComplaint': complaint,
      'answers': answers,
      'analysisSummary': summary,
      'analyzedAt': FieldValue.serverTimestamp(),
    });

    // responseId available as docRef.id if you need it in the UI.
    return summary;
  }
}

// ---------------------------------------------------------------------
// HOW TO SET THE KEY WITHOUT HARDCODING IT IN SOURCE (recommended even
// for a demo, so it doesn't end up in your public GitHub repo):
//
// Run / build with:
//   flutter run --dart-define=GROQ_API_KEY=your_key_here
//   flutter build apk --dart-define=GROQ_API_KEY=your_key_here
//
// The `String.fromEnvironment('GROQ_API_KEY', ...)` above will pick it up
// automatically — you don't need to touch the code above when doing this.
// ---------------------------------------------------------------------
```

### `test/widget_test.dart`

```dart
// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:flutterprojects/main.dart';

void main() {
  testWidgets('Counter increments smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that our counter starts at 0.
    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    // Tap the '+' icon and trigger a frame.
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    // Verify that our counter has incremented.
    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });
}
```

