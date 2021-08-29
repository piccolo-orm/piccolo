from unittest import TestCase

from piccolo.utils.dictionary import make_nested


class TestMakeNested(TestCase):
    def test_nesting(self):
        response = make_nested(
            {
                "id": 1,
                "name": "Pythonistas",
                "manager.id": 1,
                "manager.name": "Guido",
                "manager.car.colour": "green",
            }
        )
        self.assertEqual(
            response,
            {
                "id": 1,
                "name": "Pythonistas",
                "manager": {
                    "id": 1,
                    "name": "Guido",
                    "car": {"colour": "green"},
                },
            },
        )
