from demo.app import run_check

# Test ALLOW
allow_result = run_check("The cat sat on the mat", "The cat is on the mat", 0.5)
print("ALLOW:", allow_result)
assert 'background-color: #064e3b' in allow_result
assert 'ALLOW' in allow_result

# Test WARN
warn_result = run_check("different text", "other text", 0.5)
print("WARN:", warn_result)
assert 'background-color: #78350f' in warn_result
assert 'WARN' in warn_result

# Test BLOCK
block_result = run_check("hello", "hello", 0.5)
print("BLOCK:", block_result)
assert 'background-color: #7f1d1d' in block_result
assert 'BLOCK' in block_result

# Test ERROR
error_result = run_check("", "text", 0.5)
print("ERROR:", error_result)
assert 'background-color: #374151' in error_result
assert 'ERROR' in error_result

print("\nAll inline style tests passed!")