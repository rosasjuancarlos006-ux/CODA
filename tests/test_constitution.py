from pathlib import Path

def test_constitution_rule_4_allows_controller_and_mock_tests():
    """
    Verifica que la Regla 4 de docs/constitution.md haya sido formalmente enmendada
    para autorizar pruebas unitarias del controlador y contratos de presentación
    utilizando vistas simuladas en memoria (mocks/fakes con biblioteca estándar).
    """
    constitution_path = Path(__file__).resolve().parent.parent / "docs" / "constitution.md"
    assert constitution_path.exists(), "docs/constitution.md debe existir"
    
    content = constitution_path.read_text(encoding="utf-8").lower()
    
    # Debe contemplar tanto módulos puros como controlador y vistas simuladas/mocks
    assert "controlador" in content, "La constitución debe autorizar pruebas sobre el controlador"
    assert "mocks" in content or "fakes" in content, "La constitución debe autorizar vistas simuladas/mocks"
    assert "dependencias" in content, "Debe preservar la regla de cero dependencias externas"


def test_constitution_rule_1_authorizes_flet_gui_dependency():
    """
    Verifica que la Regla 1 de docs/constitution.md haya sido formalmente enmendada
    para autorizar flet como dependencia exclusiva de la capa de presentación gráfica.
    """
    constitution_path = Path(__file__).resolve().parent.parent / "docs" / "constitution.md"
    assert constitution_path.exists(), "docs/constitution.md debe existir"

    content = constitution_path.read_text(encoding="utf-8").lower()
    assert "flet" in content, "La constitución debe autorizar formalmente la dependencia flet para la capa gráfica"

    # Verificar requirements.txt
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    assert req_path.exists(), "requirements.txt debe existir"
    req_content = req_path.read_text(encoding="utf-8").lower()
    assert "flet" in req_content, "requirements.txt debe contener flet"

    # Verificar justificación en MEMORY.md
    memory_path = Path(__file__).resolve().parent.parent / "MEMORY.md"
    assert memory_path.exists(), "MEMORY.md debe existir"
    mem_content = memory_path.read_text(encoding="utf-8").lower()
    assert "flet" in mem_content, "MEMORY.md debe justificar el uso de flet"
