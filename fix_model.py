with open('main.py', 'r') as file:
    content = file.read()

# Replace any instances of the old model names with the working one
corrected_content = content.replace('claude-3-7-sonnet-20240229', 'claude-3-5-sonnet-20240620')
corrected_content = corrected_content.replace('claude-3-7-sonnet-20240608', 'claude-3-5-sonnet-20240620')

with open('main.py', 'w') as file:
    file.write(corrected_content)

print("Updated main.py to use claude-3-5-sonnet-20240620")
