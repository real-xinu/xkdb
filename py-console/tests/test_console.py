import unittest
from console import get_string


class TestConsole(unittest.TestCase):
    def test_get_string(self):
        # Test to see if we can parse null terminate strings
        test_string = b"Hello\0World!\0This is a null terminated string"

        read_cursor = 0
        string1, length = get_string(test_string[read_cursor:])

        self.assertEqual(string1, "Hello")
        self.assertEqual(length, 6)

        read_cursor += length

        string2, length = get_string(test_string[read_cursor:])
        
        self.assertEqual(string2, "World!")
        self.assertEqual(length, 7)

        read_cursor += length

        string3, length = get_string(test_string[read_cursor:])

        self.assertEqual(string3, "This is a null terminated string")
        self.assertEqual(length, 32)
