import tempfile
from pathlib import Path

from groq_agent.file_operations import FileOperations


class DummyAPIClient:
    def __init__(self):
        self.calls = []

    def generate_code_suggestions(self, file_content, prompt, model, temperature=0.3):
        self.calls.append({"file_content": file_content, "prompt": prompt})
        return file_content + "\n# edited"  # simple modification


def test_review_files_with_context():
    api = DummyAPIClient()
    ops = FileOperations(api)
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "one.py"
        file2 = Path(tmpdir) / "two.py"
        file1.write_text("print('one')\n")
        file2.write_text("print('two')\n")

        results = ops.review_files([str(file1), str(file2)], model="dummy", prompt="Add comment", auto_apply=True)

        assert all(results.values())
        assert "# edited" in file1.read_text()
        assert "# edited" in file2.read_text()

        # Ensure prompts include context from the other file
        assert "print('two')" in api.calls[0]["prompt"]
        assert "print('one')" in api.calls[1]["prompt"]
