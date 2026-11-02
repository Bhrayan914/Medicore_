import sys
from pathlib import Path

# Agrega la carpeta del proyecto al buscador de módulos de Python.
CARPETA_PROYECTO = Path(__file__).resolve().parent
if str(CARPETA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(CARPETA_PROYECTO))

from medicore.main import main

if __name__ == "__main__":
    main()
