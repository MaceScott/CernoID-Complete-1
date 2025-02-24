import os
import re
import sys

# Define project directory dynamically
project_dir = sys.argv[1] if len(sys.argv) > 1 else "CernoID-Complete"

old_imports = {
    "from gui": "from app.gui",
    "from scripts.face_detection": "from app.face_recognition.face_detection",
    "from scripts.face_encoding": "from app.face_recognition.face_encoding",
    "from scripts.face_matching": "from app.face_recognition.face_verification",
    "from scripts.camera_recognition": "from app.multi_camera.camera_recognition",
    "from app.database": "from backend.database.database",
    "from app.api": "from backend.api.api_routes",
    "from app.config": "from config.config"
}

# Track modified files
modified_files = []

for root, _, files in os.walk(project_dir):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, IOError) as e:
                print(f"❌ Skipping file {file_path} due to error: {e}")
                continue

            original_content = content
            for old, new in old_imports.items():
                # Use regex to match the exact import lines
                content = re.sub(rf"^{old}(\s|$)", rf"{new}\1", content, flags=re.MULTILINE)

            # Only write back if content has changed
            if content != original_content:
                temp_path = file_path + ".tmp"
                try:
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    os.replace(temp_path, file_path)
                    modified_files.append(file_path)
                except IOError as e:
                    print(f"❌ Failed to write file {file_path} due to error: {e}")
                    continue

# Report results
if modified_files:
    print("✅ Import paths updated successfully in the following files:")
    print("\n".join(modified_files))
else:
    print("✅ No changes made.")
