import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from .test_custom_api import main

if __name__ == "__main__":
    print("Notice: Project has migrated to your own Custom API (not Groq). Running Custom API verification:")
    main()

