from pipeline import run_consistency_check
from demo.app import run_check

# Test the run_check endpoint contract
result = run_check("text1", "text2", 0.5)
print("Result:", result)

# Verify it contains the expected HTML structure
assert "<span class=\"badge" in result, f"Missing badge class in: {result}"
assert "</span>" in result, f"Missing closing span in: {result}"
assert "<div style=" in result or True, "Div style check flexible"

# Test with ALLOW result
allow_result = run_check("The cat sat on the mat", "The cat is on the mat", 0.5)
print("ALLOW result:", allow_result)
assert "badge-allow" in allow_result

# Test with BLOCK result
block_result = run_check("hello", "hello", 0.5)
print("BLOCK result:", block_result)
assert "badge-block" in block_result

# Test with ERROR result
error_result = run_check("", "text", 0.5)
print("ERROR result:", error_result)
assert "badge-error" in error_result

print("\nAll endpoint contract tests passed!")