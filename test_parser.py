try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript as tsjs
    import tree_sitter_python as tspy
    
    print("Imports successful!")
    
    # Try initializing (This is where it usually explodes)
    JS_LANGUAGE = Language(tsjs.language())
    PY_LANGUAGE = Language(tspy.language())
    
    parser = Parser()
    parser.set_language(JS_LANGUAGE)
    
    tree = parser.parse(b"function test() { return 1; }")
    print(f"Parse successful! Root node: {tree.root_node.type}")
    
except Exception as e:
    print("\nXXX CRITICAL ERROR XXX")
    print(e)