import os
from pathlib import Path

from groq_agent.agentic_chat import AgenticChat
from groq_agent.config import ConfigurationManager


class DummyAPI:
    def __init__(self):
        pass


class DummyFileOps:
    def __init__(self):
        self.created = None

    def create_file_from_prompt(self, file_path, model, prompt, file_type=None):
        self.created = (file_path, model, prompt, file_type)
        Path(file_path).write_text("generated content")
        return True


def test_detects_make_keyword(tmp_path):
    os.chdir(tmp_path)
    config = ConfigurationManager(config_dir=tmp_path / "cfg")
    agent = AgenticChat(config, DummyAPI())
    assert agent._is_file_modification_request("make a website")


def test_creates_file_when_none_found(tmp_path, monkeypatch):
    os.chdir(tmp_path)
    config = ConfigurationManager(config_dir=tmp_path / "cfg")
    agent = AgenticChat(config, DummyAPI())
    agent.file_ops = DummyFileOps()
    monkeypatch.setattr("groq_agent.agentic_chat.Prompt.ask", lambda *args, **kwargs: "index.html")
    response = agent._handle_file_modification_request("make a website listing schools")
    assert agent.file_ops.created[0] == "index.html"
    assert "Created new file" in response
    assert Path("index.html").exists()
