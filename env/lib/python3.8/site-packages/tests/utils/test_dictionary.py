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

    def test_name_clash(self):
        """
        In this example, `manager` and `manager.*` could potentially clash.
        Nesting should take precedence.
        """
        response = make_nested(
            {
                "id": 1,
                "name": "Pythonistas",
                "manager": 1,
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
