# prompts.py
import sys
import os

class PromptError(Exception):
    pass

class ConfirmManager:
    def __init__(self, yes: bool = False, no: bool = False, stream=None):
        """
        Args:
            yes (bool): auto-confirm all prompts.
            no (bool): auto-deny all prompts.
            stream: where to write prompts (default=sys.stderr).
                    Must be valid if interactive mode is possible.
        """
        if yes and no:
            raise PromptError("Cannot use --yes and --no together")

        self.always_yes = yes
        self.always_no = no
        self.stream = stream or sys.stderr

        # Validate: if we may prompt but stream is invalid → error
        if not (self.always_yes or self.always_no):
            if not hasattr(self.stream, "write") or self.stream.closed:
                raise PromptError("Interactive confirm requires a valid stream")

    @staticmethod
    def none() -> "ConfirmManager":
        """Return a non-interactive manager that always returns True."""
        return ConfirmManager(yes=True, stream=open(os.devnull, "w"))

    def confirm_overwrite(self, file: str, prefix: str = "File") -> bool:
        """
        Ask user whether to overwrite a file, respecting --yes/--no.
        Supports interactive [y/n/a] where 'a' means 'yes to all'.
        Returns True if overwrite is allowed, False otherwise.
        """
        # --- NEW: Check for a non-interactive environment first ---
        if not sys.stdin.isatty():
            # If in a non-interactive environment and neither flag is set,
            # raise an exception so the main CLI can handle it.
            if not self.always_yes and not self.always_no:
                raise PromptError(
                    "Interactive prompt required in a non-interactive environment."
                    " Please use --yes or --no."
                )
            # Otherwise, the --yes or --no flag will handle the response
            # as intended for automated builds.
            return self.always_yes

        # --- EXISTING INTERACTIVE PROMPT LOGIC ---
        if self.always_yes:
            return True
        if self.always_no:
            return False

        while True:
            self.stream.write(
                f"Are you sure you want to overwrite {prefix}: {file}? [y/n/a] "
            )
            self.stream.flush()
            resp = sys.stdin.readline().strip().lower()

            if resp in ("y", "yes"):
                return True
            elif resp in ("n", "no"):
                return False
            elif resp in ("a", "all"):
                self.always_yes = True
                return True
            else:
                self.stream.write("Please answer 'y', 'n', or 'a'.\n")
                self.stream.flush()