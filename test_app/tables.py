from piccolo.table import Table
from piccolo.columns import Text
from piccolo.columns.constraints import UniqueConstraint

class FooTable(Table):
    field_1 = Text()
    field_2 = Text()
    field_3 = Text()

    my_test_constraint_1 = UniqueConstraint(['field_1','field_2'])

