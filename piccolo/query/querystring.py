from copy import copy
from dataclasses import dataclass
from string import Formatter
import typing as t


@dataclass
class Fragment():
    prefix: str
    index: int = 0
    no_arg: bool = False


class QueryString():

    def __init__(self, template: str, *args: t.Any) -> None:
        """
        Example template: "WHERE {} = {}"
        """
        self.template = template
        self.args = args

    def __str__(self):
        _, bundled, combined_args = self.bundle(
            start_index=1,
            bundled=[],
            combined_args=[]
        )
        template = ''.join([
            fragment.prefix + ('' if fragment.no_arg else '{}') for fragment in bundled
        ])
        return template.format(*combined_args)

    def bundle(self, start_index=1, bundled=[], combined_args=[]):
        # Split up the string, separating by {}.
        fragments = [
            Fragment(prefix=i[0]) for i in Formatter().parse(self.template)
        ]

        for index, fragment in enumerate(fragments):
            try:
                value = self.args[index]
            except IndexError:
                # trailing element
                fragment.no_arg = True
                bundled.append(fragment)
            else:
                if type(value) == self.__class__:
                    fragment.no_arg = True
                    bundled.append(fragment)

                    start_index, _, _ = value.bundle(
                        start_index=start_index,
                        bundled=bundled,
                        combined_args=combined_args,
                    )
                else:
                    fragment.index = start_index
                    bundled.append(fragment)
                    start_index += 1
                    combined_args.append(value)

        return (start_index, bundled, combined_args)

    def compile_string(self):
        """
        Compiles the template ready for Postgres - keeping the arguments
        separate from the template.
        """
        _, bundled, combined_args = self.bundle(
            start_index=1,
            bundled=[],
            combined_args=[]
        )
        string = ''.join([
            fragment.prefix + ('' if fragment.no_arg else f'${fragment.index}') for fragment in bundled
        ])
        return (string, combined_args)
