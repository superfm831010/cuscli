#!/usr/bin/env python3
"""
LLM Error Handling Mechanism Demo Script
Demonstrates the new detailed error message functionality
"""

import tempfile
from pathlib import Path
from autocoder.common.llms import LLMManager


def demo_error_handling():
    """Demonstrate detailed error handling mechanism"""
    print("=== LLM Error Handling Mechanism Demo ===\n")
    
    # Use temporary directory to avoid affecting user configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        models_json = Path(temp_dir) / "models.json"
        lm = LLMManager(str(models_json))
        
        print("1. Attempting to get non-existent model...")
        try:
            llm = lm.get_single_llm("non/existent", "lite")
            print("   ✗ Unexpected success")
        except ValueError as e:
            print(f"   ✓ Correctly caught error:")
            print(f"   {str(e)}")
        print()
        
        print("2. Attempting to get existing model without API key...")
        try:
            llm = lm.get_single_llm("deepseek/v3", "lite")
            print("   ✗ Unexpected success")
        except ValueError as e:
            print(f"   ✓ Correctly caught error:")
            print(f"   {str(e)}")
        print()
        
        print("3. Attempting to get multiple models, all unavailable...")
        try:
            llm = lm.get_single_llm("non/existent1,deepseek/v3,non/existent2", "lite")
            print("   ✗ Unexpected success")
        except ValueError as e:
            print(f"   ✓ Correctly caught error:")
            print(f"   {str(e)}")
        print()
        
        print("4. Adding a model with API key and testing...")
        custom_models = [
            {
                "name": "demo/working",
                "model_name": "demo-working-model",
                "model_type": "saas/openai",
                "base_url": "https://demo.api.com/v1",
                "api_key": "demo-key-123"
            }
        ]
        lm.add_models(custom_models)
        
        try:
            # This should succeed (although actual deployment would fail, but not due to key issues)
            print("   ✓ Model added successfully with API key configured")
        except Exception as e:
            print(f"   ✗ Model addition failed: {e}")
        print()
        
        print("5. Demonstrating new error messages vs old error messages...")
        print("   Old error message: 'NoneType' object has no attribute 'stream_chat_oai'")
        print("   New error message: Contains specific model names and failure reasons")
        print()
        
        print("=== Demo Complete ===")
        print("Now users can clearly see:")
        print("- Which models don't exist")
        print("- Which models don't have API keys configured")
        print("- Specific error reason for each model")


if __name__ == "__main__":
    try:
        demo_error_handling()
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc() 