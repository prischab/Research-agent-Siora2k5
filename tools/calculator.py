# tools/calculator.py
# The simplest tool: takes a math expression as a string, returns the result.

def calculator(expression: str) -> str:
    """
    Evaluate a math expression and return the result.
    Example: calculator("150 * 0.85") -> "127.5"
    """
    try:
        # We only allow safe math characters to avoid running arbitrary code
        allowed = set("0123456789+-*/(). ")
        if not all(char in allowed for char in expression):
            return "Error: expression contains invalid characters."

        result = eval(expression)   # safe here because we filtered the input above
        return str(result)
    except Exception as e:
        return f"Error: could not evaluate '{expression}' ({e})"


# Quick test — run this file directly to check it works
if __name__ == "__main__":
    print(calculator("150 * 0.85"))      # should print 127.5
    print(calculator("2 + 2 * 10"))      # should print 22
    print(calculator("(100 - 15) / 5"))  # should print 17.0
    print(calculator("hello"))           # should print the error message