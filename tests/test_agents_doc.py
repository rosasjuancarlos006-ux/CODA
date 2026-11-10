from pathlib import Path

def test_agents_doc_reflects_mvc_architecture():
    """
    Verifica que AGENTS.md documente la estructura modular de la arquitectura MVC:
    controllers/, ui/view_interface.py, ui/terminal_view.py, core/events.py.
    """
    agents_path = Path(__file__).resolve().parent.parent / "AGENTS.md"
    assert agents_path.exists(), "AGENTS.md debe existir"

    content = agents_path.read_text(encoding="utf-8").lower()

    assert "controllers" in content, "AGENTS.md debe documentar el paquete controllers/"
    assert "view_interface.py" in content, "AGENTS.md debe documentar ui/view_interface.py"
    assert "terminal_view.py" in content, "AGENTS.md debe documentar ui/terminal_view.py"
    assert "events.py" in content, "AGENTS.md debe documentar core/events.py"
    assert "mvc" in content, "AGENTS.md debe mencionar la arquitectura MVC"
