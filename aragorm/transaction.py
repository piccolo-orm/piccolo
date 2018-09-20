class Transaction():
    """
    Usage:

    with await Transaction() as transaction:
        transaction.add(Foo.create())
    """

    async def __aenter__(cls):
        pass

    async def __aexit__(cls):
        pass

    def __enter__(cls):
        pass

    def __exit__(cls):
        pass
