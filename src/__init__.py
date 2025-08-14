"""
Interoperability Messaging Lab Package
"""

__version__ = "0.1.0"
__author__ = "Kraig Roberts"
__email__ = "kraig.roberts@example.com"

# Import main CLI function for easy access
from .cli import main as cli_main

__all__ = ["cli_main", "__version__", "__author__", "__email__"]
