from src.utils.get_data import *

def main():
    print("=== Lancement du test ===")
    test()
    install_playwright_browsers()
    # les fonctions de get_data.py et autres fichiers dans les sous-dossiers ne peuvent être exécutées que depuis main.py

if __name__ == "__main__":
    main()