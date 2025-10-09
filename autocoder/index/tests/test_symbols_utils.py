import pytest
from autocoder.index.symbols_utils import extract_symbols, symbols_info_to_str, SymbolType, SymbolsInfo


class TestSymbolsUtils:
    """Test cases for symbols_utils module"""

    def test_extract_symbols_basic(self):
        """Test basic symbol extraction"""
        text = """用途：测试类和函数的示例代码
函数：test_method, test_function
类：TestClass
变量：value
导入语句：import os^^import json"""
        
        symbols = extract_symbols(text)
        
        assert symbols.usage == "测试类和函数的示例代码"
        assert symbols.functions == ["test_method", "test_function"]
        assert symbols.classes == ["TestClass"]
        assert symbols.variables == ["value"]
        assert symbols.import_statements == ["import os", "import json"]

    def test_extract_symbols_empty(self):
        """Test symbol extraction with empty input"""
        symbols = extract_symbols("")
        
        assert symbols.usage == ""
        assert symbols.functions == []
        assert symbols.classes == []
        assert symbols.variables == []
        assert symbols.import_statements == []

    def test_extract_symbols_null_input(self):
        """Test symbol extraction with null input"""
        symbols = extract_symbols("null")
        
        assert symbols.usage == ""
        assert symbols.functions == []
        assert symbols.classes == []
        assert symbols.variables == []
        assert symbols.import_statements == []

    def test_extract_symbols_partial(self):
        """Test symbol extraction with partial information"""
        text = """用途：部分测试代码
函数：only_function
类："""
        
        symbols = extract_symbols(text)
        
        assert symbols.usage == "部分测试代码"
        assert symbols.functions == ["only_function"]
        assert symbols.classes == []

    def test_symbols_info_to_str(self):
        """Test converting symbols info back to string"""
        symbols = SymbolsInfo(
            usage="测试用途",
            functions=["func1", "func2"],
            classes=["Class1"],
            variables=["var1", "var2"],
            import_statements=["import os", "import sys"]
        )
        
        # Test with all symbol types
        all_types = [SymbolType.USAGE, SymbolType.FUNCTIONS, SymbolType.CLASSES, 
                    SymbolType.VARIABLES, SymbolType.IMPORT_STATEMENTS]
        result = symbols_info_to_str(symbols, all_types)
        
        expected_lines = [
            "usage：测试用途",
            "functions：func1,func2",
            "classes：Class1",
            "variables：var1,var2",
            "import_statements：import os^^import sys"
        ]
        
        for line in expected_lines:
            assert line in result

    def test_symbols_info_to_str_selective(self):
        """Test converting symbols info with selective symbol types"""
        symbols = SymbolsInfo(
            usage="测试用途",
            functions=["func1", "func2"],
            classes=["Class1"],
            variables=["var1", "var2"],
            import_statements=["import os", "import sys"]
        )
        
        # Test with only functions and classes
        selected_types = [SymbolType.FUNCTIONS, SymbolType.CLASSES]
        result = symbols_info_to_str(symbols, selected_types)
        
        assert "functions：func1,func2" in result
        assert "classes：Class1" in result
        assert "usage：" not in result
        assert "variables：" not in result
        assert "import_statements：" not in result

    def test_symbols_info_to_str_empty_values(self):
        """Test converting symbols info with empty values"""
        symbols = SymbolsInfo(
            usage="",
            functions=[],
            classes=[],
            variables=["var1"],
            import_statements=[]
        )
        
        # Test with all symbol types
        all_types = [SymbolType.USAGE, SymbolType.FUNCTIONS, SymbolType.CLASSES, 
                    SymbolType.VARIABLES, SymbolType.IMPORT_STATEMENTS]
        result = symbols_info_to_str(symbols, all_types)
        
        # Only non-empty values should appear
        assert "variables：var1" in result
        # Empty values should not appear in result
        assert "usage：" not in result
        assert "functions：" not in result
        assert "classes：" not in result
        assert "import_statements：" not in result

    def test_symbol_type_enum(self):
        """Test SymbolType enum values"""
        assert SymbolType.USAGE.value == "usage"
        assert SymbolType.FUNCTIONS.value == "functions"
        assert SymbolType.VARIABLES.value == "variables"
        assert SymbolType.CLASSES.value == "classes"
        assert SymbolType.IMPORT_STATEMENTS.value == "import_statements"

    def test_extract_symbols_with_special_characters(self):
        """Test symbol extraction with special characters in names"""
        text = """用途：包含特殊字符的测试
函数：test_method_with_underscore, testMethodWithCamelCase
类：TestClass_1, AnotherClass2
变量：_private_var, PUBLIC_CONST
导入语句：from package.module import function^^import package.submodule as alias"""
        
        symbols = extract_symbols(text)
        
        assert symbols.usage == "包含特殊字符的测试"
        assert symbols.functions == ["test_method_with_underscore", "testMethodWithCamelCase"]
        assert symbols.classes == ["TestClass_1", "AnotherClass2"]
        assert symbols.variables == ["_private_var", "PUBLIC_CONST"]
        assert symbols.import_statements == [
            "from package.module import function",
            "import package.submodule as alias"
        ]

    @pytest.mark.parametrize("input_text,expected_usage", [
        ("用途：测试", "测试"),
        ("", ""),
        ("null", ""),
        ("用途：多行\n测试用途", "多行")
    ])
    def test_extract_symbols_usage_parametrized(self, input_text, expected_usage):
        """Parametrized test for usage extraction"""
        symbols = extract_symbols(input_text)
        assert symbols.usage == expected_usage

    @pytest.mark.parametrize("symbol_types,expected_in_result", [
        ([SymbolType.USAGE], ["usage："]),
        ([SymbolType.FUNCTIONS], ["functions："]),
        ([SymbolType.CLASSES], ["classes："]),
        ([SymbolType.USAGE, SymbolType.FUNCTIONS], ["usage：", "functions："]),
        ([], [])
    ])
    def test_symbols_info_to_str_parametrized(self, symbol_types, expected_in_result):
        """Parametrized test for selective symbol conversion"""
        symbols = SymbolsInfo(
            usage="测试",
            functions=["func1"],
            classes=["Class1"],
            variables=["var1"],
            import_statements=["import os"]
        )
        
        result = symbols_info_to_str(symbols, symbol_types)
        
        for expected in expected_in_result:
            assert expected in result 