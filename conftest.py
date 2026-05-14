import sys
import os

# Agrega la raíz del proyecto al path para que 'ia' y 'backend' sean importables.
# Nota: tests/ia/ NO debe tener __init__.py — evita que 'ia' resuelva a tests/ia/
# en lugar del paquete raíz ia/.
ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
