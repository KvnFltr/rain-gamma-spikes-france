from src.utils.get_data import *
from src.utils.clean_data import *

def main():
    
    print("=== Lancement du téléchargement des données ===")
    get_all_data()
    print("=== Fin du téléchargement des données ===")
    
    print("=== Lancement du nettoyage des données ===")
    clean_all_data()
    print("=== Fin du nettoyage des données ===")


if __name__ == "__main__":
    main()