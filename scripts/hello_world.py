#!/usr/bin/env python
"""
Hello World - Kiro for Claude Code Test Feature

Prosty moduł testowy weryfikujący poprawność integracji Kiro for Claude Code.
Demonstracja pełnego przepływu pracy: requirements → design → tasks → implementation.

Spec: .claude/specs/kiro-test-feature/
"""

import sys
from typing import NoReturn

# Constants
MESSAGE: str = "Hello World"
EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1


def hello_world() -> int:
    """
    Wyświetla komunikat 'Hello World' w konsoli.

    Funkcja testowa weryfikująca integrację Kiro for Claude Code.
    Demonstracja pełnego przepływu: spec → design → tasks → implementation.

    Returns:
        int: Kod wyjścia (0 = sukces, 1 = błąd)

    Raises:
        RuntimeError: Gdy wystąpi błąd podczas wyświetlania komunikatu

    Example:
        >>> result = hello_world()
        Hello World
        >>> result
        0
    """
    try:
        print(MESSAGE)
        return EXIT_SUCCESS
    except Exception as e:
        raise RuntimeError(f"Błąd podczas wyświetlania komunikatu: {e}") from e


def main() -> NoReturn:
    """
    CLI Entry Point - uruchamia funkcję hello_world i kończy proces.

    Przechwytuje kod wyjścia z hello_world() i używa sys.exit()
    do zakończenia procesu z odpowiednim kodem.

    Raises:
        SystemExit: Zawsze - z kodem 0 (sukces) lub 1 (błąd)
    """
    try:
        exit_code = hello_world()
        sys.exit(exit_code)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
