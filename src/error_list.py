class ErrorReporter:
    def __init__(self):
        self.errors = []

    def add(self, error):
        self.errors.append(str(error))

    def has_errors(self):
        return len(self.errors) > 0

    def print_errors(self):
        print("\n--- COMPILER ERRORS ---")
        for err in self.errors:
            print(err)
        print("-----------------------\n")