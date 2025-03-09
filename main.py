from scrape_01_gruposhopmix import scrape_gruposhopmix
from scrape_02_triboshoes import scrape_triboshoes
from scrape_03_modajeans import scrape_modajeans
from scrape_04_atacadum import scrape_atacadum
from scrape_05_florattajoias import scrape_florattajoias
from scrape_06_cemstoretec import scrape_06_cemstoretec


from sheets import save_to_google_sheets

if __name__ == "__main__":

    # base_url = 'https://app.gruposhopmix.com.br/login'
    # data = scrape_gruposhopmix(base_url)
    # save_to_google_sheets(data,0)
    # print("Finalizado web scraping gruposhopmix")

    # base_url = 'https://triboshoes.com.br/'  
    # data = scrape_triboshoes(base_url)
    # save_to_google_sheets(data,1)    
    # print("Finalizado web scraping triboshoes")
    
    # base_url = 'https://atacadodamodajeans.lojavirtualnuvem.com.br/produtos/?mpage=3'  
    # data = scrape_modajeans(base_url)
    # save_to_google_sheets(data,2)
    # print("Finalizado web scraping atacadodamodajeans")

    # base_url = 'https://www.atacadum.com.br/'  
    # data = scrape_atacadum(base_url)
    # save_to_google_sheets(data, 3)
    # print("Finalizado web scraping atacadum")

    # base_url = 'https://www.florattajoias.com.br/'  
    # data = scrape_florattajoias(base_url)
    # save_to_google_sheets(data, 4)
    # print("Finalizado web scraping florattajoias")

    base_url = 'https://cemstoretec.com.br/'  
    data = scrape_06_cemstoretec(base_url)
    save_to_google_sheets(data, 5)
    print("Finalizado web scraping cemstoretec")
    

    

     
    
