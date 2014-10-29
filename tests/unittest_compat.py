import re
import unittest


def assertIn(self, member, container, msg=None):
    """Just like self.assertTrue(a in b), but with a nicer default message."""
    if member not in container:
        if not msg:
            msg = '%r not found in %r' % (member, container)
        self.fail(msg)
unittest.TestCase.assertIn = assertIn

def assertNotIn(self, member, container, msg=None):
    """Just like self.assertTrue(a not in b), but with a nicer default message."""
    if member in container:
        if not msg:
            msg = '%s unexpectedly found in %s' % (member,
                                                    container)
        self.fail(msg)
unittest.TestCase.assertNotIn = assertNotIn

def assertGreater(self, a, b, msg=None):
    """Just like self.assertTrue(a > b), but with a nicer default message."""
    if not a > b:
        if not msg:
            msg = '%s not greater than %s' % (a, b)
        self.fail(msg)
unittest.TestCase.assertGreater = assertGreater

def assertRegexpMatches(self, text, expected_regexp, msg=None):
    """Fail the test unless the text matches the regular expression."""
    if isinstance(expected_regexp, basestring):
        expected_regexp = re.compile(expected_regexp)
    if not expected_regexp.search(text):
        msg = msg or "Regexp didn't match"
        msg = '%s: %r not found in %r' % (msg, expected_regexp.pattern, text)
        raise self.failureException(msg)
unittest.TestCase.assertRegex = assertRegexpMatches

def assertNotRegexpMatches(self, text, unexpected_regexp, msg=None):
    """Fail the test if the text matches the regular expression."""
    if isinstance(unexpected_regexp, basestring):
        unexpected_regexp = re.compile(unexpected_regexp)
    match = unexpected_regexp.search(text)
    if match:
        msg = msg or "Regexp matched"
        msg = '%s: %r matches %r in %r' % (msg,
                                           text[match.start():match.end()],
                                           unexpected_regexp.pattern,
                                           text)
        raise self.failureException(msg)
unittest.TestCase.assertNotRegex = assertNotRegexpMatches

def assertIsInstance(self, obj, cls, msg=None):
    """Same as self.assertTrue(isinstance(obj, cls)), with a nicer
    default message."""
    if not isinstance(obj, cls):
        if not msg:
            msg = '%s is not an instance of %r' % (obj, cls)
        self.fail(msg)
unittest.TestCase.assertIsInstance = assertIsInstance
