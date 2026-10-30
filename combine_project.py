"""
combine_project.py

Usage:
    python combine_project.py <project_folder_path> [output_file.txt]

Example:
    python combine_project.py "C:\\Users\\Abdullah\\Desktop\\NeuroBridge" project_combined.txt
    python combine_project.py "/home/user/neurobridge_app"

Ye script aapke pure project folder ke andar se sab relevant code files
(dart, py, js, ts, json, yaml, etc.) dhoond kar aik hi .txt file mein
jama kar deta hai, taake aap wo file Claude ko bhej sakein.

Ye automatically chhor deta hai:
- build/, .dart_tool/, .git/, node_modules/, .idea/, .vscode/
- Android/iOS generated/binary folders
- images, fonts, aur binary files
- bohat bari files (5MB se zyada)
"""

import os
import sys

# File extensions jo hum include karenge (source code / config)
INCLUDE_EXTENSIONS = {
    ".dart", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".yaml", ".yml", ".gradle", ".xml",
    ".md", ".env", ".txt", ".kt", ".java", ".swift",
    ".gitignore", ".plist", ".toml", ".properties"
}

# Folders jo hum skip karenge
EXCLUDE_DIRS = {
    "build", ".dart_tool", ".git", "node_modules", ".idea",
    ".vscode", "Pods", "DerivedData", ".gradle", "gradle",
    "android/app/build", "ios/build", ".flutter-plugins",
    "coverage", "__pycache__", ".venv", "venv"
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def should_skip_dir(dirname: str) -> bool:
    return dirname in EXCLUDE_DIRS or dirname.startswith(".")


def is_probably_lockfile_or_binary(filename: str) -> bool:
    lock_or_binary_names = {
        "pubspec.lock", "package-lock.json", "yarn.lock",
        "Podfile.lock", ".DS_Store"
    }
    return filename in lock_or_binary_names


def combine_project(project_path: str, output_path: str) -> None:
    if not os.path.isdir(project_path):
        print(f"Error: '{project_path}' ek valid folder nahi hai.")
        sys.exit(1)

    files_written = 0
    files_skipped_size = 0
    files_skipped_type = 0

    with open(output_path, "w", encoding="utf-8", errors="replace") as out_file:
        out_file.write(f"PROJECT COMBINED SOURCE DUMP\n")
        out_file.write(f"Source folder: {project_path}\n")
        out_file.write("=" * 80 + "\n\n")

        for root, dirs, files in os.walk(project_path):
            # Prune excluded directories in-place so os.walk skips them
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]

            for filename in sorted(files):
                ext = os.path.splitext(filename)[1].lower()

                if is_probably_lockfile_or_binary(filename):
                    files_skipped_type += 1
                    continue

                if ext not in INCLUDE_EXTENSIONS:
                    files_skipped_type += 1
                    continue

                full_path = os.path.join(root, filename)

                try:
                    file_size = os.path.getsize(full_path)
                except OSError:
                    continue

                if file_size > MAX_FILE_SIZE_BYTES:
                    files_skipped_size += 1
                    continue

                rel_path = os.path.relpath(full_path, project_path)

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception as e:
                    content = f"[Could not read file: {e}]"

                out_file.write(f"\n{'#' * 80}\n")
                out_file.write(f"# FILE: {rel_path}\n")
                out_file.write(f"{'#' * 80}\n\n")
                out_file.write(content)
                out_file.write("\n")

                files_written += 1

    print(f"Done! Combined file bana diya: {output_path}")
    print(f"  - Files included: {files_written}")
    print(f"  - Files skipped (wrong type/lockfile): {files_skipped_type}")
    print(f"  - Files skipped (too large): {files_skipped_size}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python combine_project.py <project_folder_path> [output_file.txt]")
        sys.exit(1)

    project_folder = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "project_combined.txt"

    combine_project(project_folder, output_file)