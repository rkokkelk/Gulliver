from twisted.trial import unittest

from deluge.decorators import proxy


class DecoratorsTestCase(unittest.TestCase):
    def test_proxy_with_simple_functions(self):
        def negate(func, *args, **kwargs):
            return not func(*args, **kwargs)

        @proxy(negate)
        def something(bool):
            return bool

        @proxy(negate)
        @proxy(negate)
        def double_nothing(bool):
            return bool

        self.assertTrue(something(False))
        self.assertFalse(something(True))
        self.assertTrue(double_nothing(True))
        self.assertFalse(double_nothing(False))

    def test_proxy_with_class_method(self):
        def negate(func, *args, **kwargs):
            return -func(*args, **kwargs)

        class Test(object):
            def __init__(self, number):
                self.number = number

            @proxy(negate)
            def diff(self, number):
                return self.number - number

            @proxy(negate)
            def no_diff(self, number):
                return self.diff(number)

        t = Test(5)
        self.assertEqual(t.diff(1), -4)
        self.assertEqual(t.no_diff(1), 4)
