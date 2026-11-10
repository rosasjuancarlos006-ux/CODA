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
