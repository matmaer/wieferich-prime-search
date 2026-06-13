from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]


try:
    __version__ = version("wieferich-prime")

except PackageNotFoundError:
    __version__ = "dev"
