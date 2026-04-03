from utils import format_output_for_mobile

def test_format_output_for_mobile():
    # Long text with tables and code blocks
    text = (
        "Project Stats:\n"
        "| File | Size | Type |\n"
        "| --- | --- | --- |\n"
        "| main.py | 100kb | Code |\n"
        "\n"
        "A very long line that should be wrapped because it exceeds the fifty character limit set for mobile devices like the MSI Claw.\n"
        "\n"
        "```python\n"
        "def hello_world():\n"
        "    print('This line should not be wrapped even if it is very long and exceeds the fifty character limit.')\n"
        "```"
    )

    formatted = format_output_for_mobile(text, max_width=50, max_length=1000)
    print("--- Formatted Output ---")
    print(formatted)
    print("--- End ---")

    # Check for wrapping in normal text
    assert "exceeds the fifty character limit set for mobile\ndevices like the MSI Claw." in formatted

    # Check for code block preservation
    assert "print('This line should not be wrapped even if it is very long and exceeds the fifty character limit.')" in formatted

    # Check for table replacement
    assert "| File |" not in formatted
    assert "**File**: main.py" in formatted

    # Check for truncation
    text_long = "X" * 4000
    formatted_long = format_output_for_mobile(text_long, max_length=100)
    assert len(formatted_long) <= 100
    assert formatted_long.endswith("...")

    print("✅ All tests passed!")

if __name__ == "__main__":
    test_format_output_for_mobile()
