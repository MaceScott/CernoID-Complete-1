import os
import re

def update_imports(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin1') as f:
                content = f.read()
        except:
            print(f"Failed to read file: {file_path}")
            return
    
    # Replace imports from errors to decorators
    content = re.sub(
        r'from .*\.errors import handle_errors',
        'from ..utils.decorators import handle_errors',
        content
    )
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except:
        print(f"Failed to write file: {file_path}")

def main():
    base_dir = os.path.join('backend', 'src')
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_imports(file_path)

if __name__ == '__main__':
    main() 