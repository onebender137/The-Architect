import textwrap
import re

def format_output_for_mobile(text: str, max_width: int = 50, max_length: int = 3000) -> str:
    """
    Formats text for mobile display:
    - Wraps text to a maximum width (except for code blocks).
    - Truncates text to a maximum length.
    - Replaces markdown tables with bolded key-value lists (best effort).
    """
    if not text:
        return ""

    # Split into code blocks and normal text
    # This regex looks for triple backtick blocks
    parts = re.split(r'(```[\s\S]*?```)', text)
    formatted_parts = []

    for part in parts:
        if part.startswith("```"):
            # It's a code block, keep it as is (no wrapping, no table replacement)
            formatted_parts.append(part)
        else:
            # Normal text: replace tables and wrap
            lines = part.splitlines()
            processed_lines = []
            in_table = False
            headers = []

            for line in lines:
                if line.strip().startswith("|") and "|" in line:
                    table_parts = [p.strip() for p in line.split("|") if p.strip()]
                    if not in_table:
                        in_table = True
                        headers = table_parts
                    else:
                        if all(all(c in "- :" for c in p) for p in table_parts):
                            continue
                        for i, p in enumerate(table_parts):
                            header = headers[i] if i < len(headers) else f"Col {i+1}"
                            processed_lines.append(f"**{header}**: {p}")
                        processed_lines.append("")
                else:
                    in_table = False
                    processed_lines.append(line)

                # Wrap the processed lines immediately if they aren't part of a table row
                # (Actually, it's easier to wrap after processing all lines in this non-code part)

            temp_text = "\n".join(processed_lines)
            wrapped_lines = []
            for line in temp_text.splitlines():
                if line.strip():
                    wrapped_lines.extend(textwrap.wrap(line, width=max_width, break_long_words=False, replace_whitespace=False))
                else:
                    wrapped_lines.append("")
            formatted_parts.append("\n".join(wrapped_lines))

    final_text = "".join(formatted_parts)

    # Truncate
    if len(final_text) > max_length:
        final_text = final_text[:max_length-3] + "..."

    return final_text
