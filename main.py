from src.utils.get_data import *
from src.utils.clean_data import *

def main():
    
    #print("=== Start downloading data ===")
    #get_all_data()
    #print("=== Data download complete ===")
    
    print("=== Start cleaning up data ===")
    clean_all_data()
    print("=== Data cleaning complete ===")
    

if __name__ == "__main__":
    main()