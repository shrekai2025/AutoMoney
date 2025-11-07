"""Check if OnChainAgent has the fix"""

# Read the current onchain_agent.py file
with open("/Users/uniteyoo/Documents/AutoMoney/AMbackend/app/agents/onchain_agent.py", "r") as f:
    content = f.read()

print("=" * 80)
print("🔍 Checking OnChainAgent Code")
print("=" * 80)

# Check for the bug
if "messages=[m.dict() for m in messages]" in content:
    print("\n❌ ❌ ❌ BUG STILL EXISTS!")
    print("   Line 43 still has the bug: messages=[m.dict() for m in messages]")
    print("   Backend needs to be restarted to use the fixed code!")
else:
    print("\n✅ ✅ ✅ BUG IS FIXED!")
    print("   Line 43 has been corrected to: messages=messages")

# Check for confidence_level fix
if "'confidence_level' not in result_dict" in content:
    print("\n✅ confidence_level auto-calculation is present")
else:
    print("\n❌ confidence_level fix is missing")

# Check line 43 specifically
lines = content.split("\n")
for i, line in enumerate(lines, 1):
    if "llm_manager.chat_for_agent" in line:
        print(f"\n📍 Line {i}: {line.strip()}")
        # Print surrounding lines
        for j in range(max(0, i-2), min(len(lines), i+3)):
            print(f"   {j+1}: {lines[j]}")

print("\n" + "=" * 80)
print("💡 IMPORTANT:")
print("   If the bug is fixed but backend is not restarted,")
print("   the OLD buggy code is still running in memory!")
print("   Please restart the backend: uvicorn app.main:app --reload")
print("=" * 80)
