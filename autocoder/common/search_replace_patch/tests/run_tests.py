#!/usr/bin/env python3
"""
Test runner for Search Replace Patch module
"""

import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .test_base import TestReplaceStrategy, TestReplaceResult, TestBaseReplacer
from .test_regex_replacer import TestRegexReplacer
from .test_similarity_replacer import TestSimilarityReplacer
from .test_patch_replacer import TestPatchReplacer
from .test_manager import TestSearchReplaceManager
from .test_integration import TestSearchReplacePatchIntegration


def create_test_suite():
    """Create a test suite with all tests"""
    suite = unittest.TestSuite()
    
    # Add base tests
    suite.addTest(unittest.makeSuite(TestReplaceStrategy))
    suite.addTest(unittest.makeSuite(TestReplaceResult))
    suite.addTest(unittest.makeSuite(TestBaseReplacer))
    
    # Add replacer tests
    suite.addTest(unittest.makeSuite(TestRegexReplacer))
    suite.addTest(unittest.makeSuite(TestSimilarityReplacer))
    suite.addTest(unittest.makeSuite(TestPatchReplacer))
    
    # Add manager tests
    suite.addTest(unittest.makeSuite(TestSearchReplaceManager))
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(TestSearchReplacePatchIntegration))
    
    return suite


def run_specific_test(test_class_name=None, test_method_name=None):
    """Run a specific test class or method"""
    if test_class_name:
        # Map test class names to actual classes
        test_classes = {
            'TestReplaceStrategy': TestReplaceStrategy,
            'TestReplaceResult': TestReplaceResult,
            'TestBaseReplacer': TestBaseReplacer,
            'TestRegexReplacer': TestRegexReplacer,
            'TestSimilarityReplacer': TestSimilarityReplacer,
            'TestPatchReplacer': TestPatchReplacer,
            'TestSearchReplaceManager': TestSearchReplaceManager,
            'TestSearchReplacePatchIntegration': TestSearchReplacePatchIntegration
        }
        
        if test_class_name in test_classes:
            test_class = test_classes[test_class_name]
            
            if test_method_name:
                # Run specific method
                suite = unittest.TestSuite()
                suite.addTest(test_class(test_method_name))
                return suite
            else:
                # Run all methods in the class
                return unittest.makeSuite(test_class)
        else:
            print(f"Test class '{test_class_name}' not found")
            print(f"Available test classes: {list(test_classes.keys())}")
            return None
    else:
        return create_test_suite()


def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Search Replace Patch tests')
    parser.add_argument('--test-class', help='Run specific test class')
    parser.add_argument('--test-method', help='Run specific test method (requires --test-class)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--failfast', '-f', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Create test suite
    suite = run_specific_test(args.test_class, args.test_method)
    
    if suite is None:
        return 1
    
    # Configure test runner
    runner = unittest.TextTestRunner(
        verbosity=2 if args.verbose else 1,
        failfast=args.failfast
    )
    
    # Run tests
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main()) 