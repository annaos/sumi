import unittest
from unittest.mock import patch, mock_open
import json
from datetime import timedelta

from src.core.get_chat_history import get_chat_history_by_message_id, get_chat_history_by_timestamp

class MyTestCase(unittest.TestCase):

    sample_json = {
      "chat_id": -123,
      "summary_created_at": "2024-07-15T23:50:47.117097",
      "cleaned_at": "2024-07-15T20:50:58.147062",
      "messages": [
        {
          "message_id": 10,
          "timestamp": "2024-07-12T14:24:55.493818",
          "sender": "Anna Os",
          "message": "First"
        },
        {
          "message_id": 11,
          "timestamp": "2024-07-13T14:24:55.493818",
          "sender": "Sven",
          "message": "Second"
        },
        {
          "message_id": 16,
          "timestamp": "2024-07-14T14:24:55.493818",
          "sender": "Anna Os",
          "message": "Third message"
        }
      ]
    }

    filtered_json = {
      "chat_id": -123,
      "summary_created_at": "2024-07-15T23:50:47.117097",
      "cleaned_at": "2024-07-15T20:50:58.147062",
      "messages": [
        {
          "message_id": 11,
          "timestamp": "2024-07-13T14:24:55.493818",
          "sender": "Sven",
          "message": "Second"
        },
        {
          "message_id": 16,
          "timestamp": "2024-07-14T14:24:55.493818",
          "sender": "Anna Os",
          "message": "Third message"
        }
      ]
    }

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps(sample_json))
    def test_by_message_id(self, mock_file):
        actual_output = get_chat_history_by_message_id(123, 11)
        self.assertEqual(self.filtered_json, actual_output)

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps(sample_json))
    def test_by_timestamp(self, mock_file):
        actual_output = get_chat_history_by_timestamp(123, "2024-07-13T11:24:55.493818")
        self.assertEqual(self.filtered_json, actual_output)




if __name__ == '__main__':
    unittest.main()
