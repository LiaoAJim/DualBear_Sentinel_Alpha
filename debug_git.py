import subprocess
import sys

def run():
    try:
        result = subprocess.run(["git", "status"], capture_output=True, text=True, check=False)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print("EXIT CODE:", result.returncode)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    run()
