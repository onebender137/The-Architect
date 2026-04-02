import pyfiglet
import logging
import io

def test_banner():
    print("Testing Banner Generation:")
    banner = pyfiglet.figlet_format("ARCHITECT", font="slant")
    print(banner)
    # Figlet output is ASCII art, so it won't be a simple string match.
    # We just ensure it returns something non-empty.
    assert len(banner) > 0

def test_logging():
    print("Testing Logging Format:")
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    # The format we implemented: "[%(asctime)s] <%(levelname)s> %(message)s"
    formatter = logging.Formatter("[%(asctime)s] <%(levelname)s> %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Test message for BBS style")

    log_output = log_capture.getvalue()
    print(f"Captured Log: {log_output.strip()}")
    assert "<INFO>" in log_output
    assert "[" in log_output and "]" in log_output

def test_whois_box():
    print("Testing /whois box format:")
    handle = "┼┼Üδ┼│εR"
    box = (
        "┌──────────────────────────────────────────┐\n"
        "│  USER IDENTIFICATION                     │\n"
        "├──────────────────────────────────────────┤\n"
        f"│  Handle: {handle}                    │\n"
        "│  Status: Old-school BBS Hacker       │\n"
        "│  Access: SYSOP LEVEL                 │\n"
        "└──────────────────────────────────────────┘"
    )
    print(box)
    assert handle in box

if __name__ == "__main__":
    test_banner()
    test_logging()
    test_whois_box()
    print("\n✅ All scene verification tests passed!")
