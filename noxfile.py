import nox
from nox.sessions import Session


@nox.session(python=["3.10"])
def flake8(session: Session) -> None:
    session.install(
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-bugbear",
    )
    session.run("flake8", "fastapi_tarpit/")


@nox.session(python=["3.10"])
def isort(session: Session) -> None:
    session.install("isort")
    session.run("isort", "--check", "--diff", "fastapi_tarpit/")


@nox.session(python=["3.10"])
def mypy(session: Session) -> None:
    requirements = \
            nox.project.load_toml("pyproject.toml")["project"]["dependencies"]
    session.install(*requirements)
    session.install("mypy")
    session.run("mypy", "--strict", "fastapi_tarpit/")
