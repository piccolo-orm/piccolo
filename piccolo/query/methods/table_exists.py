from ..base import Query


class TableExists(Query):

    def response_handler(self, response):
        return response[0]['exists']

    def __str__(self):
        return (
            "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE "
            f"table_name = '{self.table.Meta.tablename}')"
        )
