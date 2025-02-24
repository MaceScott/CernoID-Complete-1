def clean_requirements():
    """Clean requirements file of hidden characters and Windows packages"""
    # Read the requirements file
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        reqs = f.readlines()

    # Clean each line
    cleaned_reqs = []
    for req in reqs:
        # Remove hidden characters and whitespace
        clean_req = req.strip().replace('\r', '').replace('\n', '').replace('਍', '').replace('ഀ', '')
        
        # Skip empty lines
        if not clean_req:
            continue
            
        # Skip Windows-specific packages
        if 'pywin32' in clean_req.lower():
            continue
            
        cleaned_reqs.append(clean_req)

    # Write cleaned requirements
    with open('requirements.docker.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_reqs))

    print("Created clean requirements.docker.txt")
    print(f"Total packages: {len(cleaned_reqs)}")

if __name__ == '__main__':
    clean_requirements() 