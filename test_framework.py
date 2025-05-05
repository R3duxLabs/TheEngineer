"""
Test framework for The Engineer application.
Provides utilities for testing various components of the application.
"""

import os
import json
import sys
import logging
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class EngineerTestCase(unittest.TestCase):
    """Base test case for The Engineer tests"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for test data
        self.test_dir = tempfile.mkdtemp()
        self.conversations_dir = os.path.join(self.test_dir, 'conversations')
        self.prompts_dir = os.path.join(self.test_dir, 'prompts')
        self.settings_dir = os.path.join(self.test_dir, 'settings')
        self.exports_dir = os.path.join(self.test_dir, 'exports')
        
        os.makedirs(self.conversations_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        os.makedirs(self.settings_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        
        # Patch environment variables
        self.env_patcher = patch.dict('os.environ', {
            'ANTHROPIC_API_KEY': 'mock_api_key'
        })
        self.env_patcher.start()
        
        # Sample conversation data for testing
        self.sample_conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
            {"role": "user", "content": "What can you do?"},
            {"role": "assistant", "content": "I can help you with coding tasks, answer questions, and analyze files."}
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
        
        # Stop patchers
        self.env_patcher.stop()

    def create_test_conversation_file(self, filename='test_conversation.json'):
        """Create a test conversation file"""
        filepath = os.path.join(self.conversations_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.sample_conversation, f)
        return filepath

    def mock_api_response(self, status_code=200, json_data=None):
        """Create a mock API response"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {
            "content": [{"text": "This is a mock response from Claude."}]
        }
        mock_response.text = json.dumps(mock_response.json.return_value)
        return mock_response


class ConversationTests(EngineerTestCase):
    """Tests for conversation functionality"""
    
    def test_save_conversation(self):
        """Test saving a conversation"""
        from main import save_conversation
        
        with patch('main.CONVERSATION_DIR', self.conversations_dir):
            # Save the conversation
            filepath = save_conversation(self.sample_conversation, 'test_save.json')
            
            # Check if file was created
            self.assertTrue(os.path.exists(filepath))
            
            # Check file contents
            with open(filepath, 'r') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data, self.sample_conversation)
    
    def test_load_conversation(self):
        """Test loading a conversation"""
        from main import load_conversation
        
        # Create test file
        filepath = self.create_test_conversation_file()
        filename = os.path.basename(filepath)
        
        with patch('main.CONVERSATION_DIR', self.conversations_dir):
            # Load the conversation
            loaded_data = load_conversation(filename)
            
            # Check loaded data
            self.assertEqual(loaded_data, self.sample_conversation)


class SearchTests(EngineerTestCase):
    """Tests for search functionality"""
    
    def test_search_conversations(self):
        """Test searching conversations"""
        from search import search_conversations
        
        # Create test files
        self.create_test_conversation_file('conv1.json')
        
        # Test search
        results = search_conversations("help", self.conversations_dir)
        
        # Verify results
        self.assertTrue(len(results) > 0)
        self.assertIn('matches', results[0])
        self.assertTrue(len(results[0]['matches']) > 0)


class ExportTests(EngineerTestCase):
    """Tests for export functionality"""
    
    def test_export_json(self):
        """Test exporting conversation to JSON"""
        from export_import import export_json
        
        # Export to JSON
        filepath = os.path.join(self.exports_dir, 'export_test.json')
        export_json(self.sample_conversation, filepath)
        
        # Check if file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check file contents
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.assertIn('messages', data)
            self.assertEqual(data['messages'], self.sample_conversation)


class SettingsTests(EngineerTestCase):
    """Tests for settings functionality"""
    
    def test_initialize_settings(self):
        """Test initializing settings"""
        from settings import initialize_settings
        
        with patch('settings.SETTINGS_DIR', self.settings_dir):
            # Initialize settings
            settings = initialize_settings()
            
            # Check default settings
            self.assertIsInstance(settings, dict)
            self.assertIn('domain', settings)
            self.assertIn('model', settings)


class APITests(EngineerTestCase):
    """Tests for API functionality"""
    
    def test_call_claude(self):
        """Test calling Claude API"""
        from main import call_claude
        
        # Mock the API response
        mock_response = self.mock_api_response()
        
        with patch('requests.post', return_value=mock_response):
            # Call the API
            result, conversation = call_claude("Test message", self.sample_conversation)
            
            # Check result
            self.assertEqual(result, "This is a mock response from Claude.")
            
            # Check conversation was updated
            self.assertEqual(len(conversation), len(self.sample_conversation) + 2)
            self.assertEqual(conversation[-2]['role'], 'user')
            self.assertEqual(conversation[-2]['content'], 'Test message')


def run_tests():
    """Run all tests"""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(ConversationTests))
    suite.addTest(loader.loadTestsFromTestCase(SearchTests))
    suite.addTest(loader.loadTestsFromTestCase(ExportTests))
    suite.addTest(loader.loadTestsFromTestCase(SettingsTests))
    suite.addTest(loader.loadTestsFromTestCase(APITests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run all tests
    success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)