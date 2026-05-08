#!/usr/bin/env python3
"""Script para descargar recursos NLTK necesarios en el build/container.

Ejecutar durante el Docker build o en el entrypoint para asegurar que
los recursos están disponibles antes de arrancar la app.
"""

import nltk

RESOURCES = ["punkt"]


def main():
    for r in RESOURCES:
        nltk.download(r)


if __name__ == "__main__":
    main()
