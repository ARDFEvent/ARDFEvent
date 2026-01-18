from sqlalchemy.orm import Session
from sqlalchemy import Delete, Select

from models import Runner, Category


class RunnerToImport:
    def __init__(
        self,
        name: str,
        reg: str,
        si: int,
        category_name: str,
        call: str,
    ) -> None:
        self.name = name
        self.reg = reg
        self.si = si
        self.category_name = category_name
        self.call = call


# ERR 1: Rewrite
# ERR 2: No category
# ERR 3: Invalid club


def import_runners(db, data: list[RunnerToImport], clubs: dict[str, str]):
    sess = Session(db, autoflush=False)
    for runner in data:
        if sess.scalars(Select(Runner).where(Runner.reg == runner.reg)).all():
            yield (1, runner)
            sess.execute(Delete(Runner).where(Runner.reg == runner.reg))

        categories = sess.scalars(
            Select(Category).where(Category.name == runner.category_name)
        ).all()
        if not categories:
            yield (2, runner)
            category = Category(name=runner.category_name)
            sess.add(category)
        else:
            category = categories[0]

        club_reg = runner.reg[:3]
        if club_reg in clubs:
            club = clubs[club_reg]
        else:
            yield (3, runner)
            club = ""

        sess.add(
            Runner(
                name=runner.name,
                reg=runner.reg,
                si=runner.si,
                category=category,
                call=runner.call,
                club=club,
            )
        )

        if club != "":
            yield (0, runner)

        sess.commit()

    sess.close()
