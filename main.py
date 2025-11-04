import sys
from pydantic import BaseModel



def main():
    print("Hello from summaryagent!")


if __name__ == "__main__":
    print(sys.executable)
    print(sys.version_info)
    print([p for p in sys.path if 'site-packages' in p])
    main()
