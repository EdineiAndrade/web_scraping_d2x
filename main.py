from scrape_01_gruposhopmix import scrape_gruposhopmix
from scrape_02_triboshoes import scrape_triboshoes
from scrape_03_modajeans import scrape_modajeans

from sheets import save_to_google_sheets

if __name__ == "__main__":

    base_url = 'https://atacadodamodajeans.lojavirtualnuvem.com.br/produtos/?mpage=3'  
    data = scrape_modajeans(base_url)
    save_to_google_sheets(data,2)
    print("Finalizado web scraping atacadodamodajeans")

    # base_url = 'https://triboshoes.com.br/'  
    # data = scrape_triboshoes(base_url)
    # save_to_google_sheets(data,1)    

    # base_url = 'https://app.gruposhopmix.com.br/login'
    # data = scrape_gruposhopmix(base_url)
    # save_to_google_sheets(data,0)
    
     
    
