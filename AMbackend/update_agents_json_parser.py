"""Script to update all agents to use the robust JSON parser"""

import re

agents_to_update = [
    "app/agents/super_agent.py",
    "app/agents/macro_agent.py",
    "app/agents/general_analysis_agent.py",
]

for agent_file in agents_to_update:
    print(f"\nUpdating {agent_file}...")

    with open(agent_file, 'r') as f:
        content = f.read()

    # Add import if not present
    if "from app.utils.json_parser import" not in content:
        # Find the imports section and add our import
        import_section_end = content.find('\n\n\nclass')
        if import_section_end == -1:
            import_section_end = content.find('\n\nclass')

        if import_section_end != -1:
            before = content[:import_section_end]
            after = content[import_section_end:]

            # Remove existing json import if present
            before = re.sub(r'import json\n', '', before)

            # Add our import
            before += "\nfrom app.utils.json_parser import parse_llm_json, JSONParseError"

            content = before + after

    # Replace old JSON parsing pattern with new one
    old_pattern = r'''try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            if "```json" in content:
                json_start = content\.find\("```json"\) \+ 7
                json_end = content\.find\("```", json_start\)
                json_str = content\[json_start:json_end\]\.strip\(\)
            elif "```" in content:
                json_start = content\.find\("```"\) \+ 3
                json_end = content\.find\("```", json_start\)
                json_str = content\[json_start:json_end\]\.strip\(\)
            else:
                # Assume entire response is JSON
                json_str = content\.strip\(\)

            # Parse JSON
            analysis = json\.loads\(json_str\)'''

    new_pattern = '''try:
            # Use robust JSON parser
            analysis = parse_llm_json(content, expected_fields=required_fields)'''

    content = re.sub(old_pattern, new_pattern, content, flags=re.DOTALL)

    # Also replace simple json.loads patterns
    content = re.sub(
        r'json\.loads\(json_str\)',
        'parse_llm_json(content)',
        content
    )

    # Replace JSONDecodeError with JSONParseError
    content = re.sub(
        r'\(json\.JSONDecodeError, ValueError\)',
        '(JSONParseError, ValueError)',
        content
    )

    with open(agent_file, 'w') as f:
        f.write(content)

    print(f"  ✓ Updated {agent_file}")

print("\n✅ All agents updated!")
