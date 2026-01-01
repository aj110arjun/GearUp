import os
import re

def replace_date_formats(directory):
    patterns = [
        (re.compile(r'\|date:"F j, Y"'), '|date:"d/m/Y"'),
        (re.compile(r'\|date:"M d, Y"'), '|date:"d/m/Y"'),
        (re.compile(r'\|date:"F d, Y"'), '|date:"d/m/Y"'),
        (re.compile(r'\|date:"M d, Y H:i"'), '|date:"d/m/Y H:i"'),
        (re.compile(r'\|date:"d M Y, H:i"'), '|date:"d/m/Y H:i"'),
        (re.compile(r'\|date:"M d, Y g:i A"'), '|date:"d/m/Y H:i"'),
        (re.compile(r'\|date:"g:i A"'), '|date:"H:i"'),
        (re.compile(r'\|date:"h:i A"'), '|date:"H:i"'),
    ]

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                new_content = content
                for pattern, replacement in patterns:
                    new_content = pattern.sub(replacement, new_content)
                
                if new_content != content:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"Updated: {file_path}")

if __name__ == "__main__":
    replace_date_formats('/home/arjun-aj/Documents/django/project3/src/GearUp/templates')
