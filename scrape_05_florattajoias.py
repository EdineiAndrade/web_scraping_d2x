from sheets import save_to_google_sheets
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re

# Função para salvar os dados em um arquivo Excel
def save_to_sheets(data):    
    #data.to_excel(filename, index=False)
    save_to_google_sheets(data,4)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page):
    try:
        # Extrair informações usando os seletores fornecidos
        time.sleep(2)
        tag_categoria = page.query_selector_all('//*[@class="container-produto"]/section/ul/li/a')
        lista_categoria = list(map(lambda link: link.inner_text(), tag_categoria))
        nome_categiria = ">".join(lista_categoria[1:])
        categoria = nome_categiria.title()

        produto = page.locator('//*[@class="produto-infos"]/p[1]').inner_text().title()
        print(f"Processando categoria: {categoria} | produto:{produto}")
        
        codigo = page.locator('//*[@class="produto-infos"]/p[2]').inner_text().replace('Ref.: ','')        
        preco_str = page.locator('//*[@class="v"]').inner_text().replace('.','').replace(',','.')
        preco_venda = str(round(float(preco_str)* 1.1,2))
        imagem = page.query_selector_all('//*[@class="slick-track"]//img')
        lista_imagens = list(map(lambda link: link.get_attribute('src'), imagem))     
        lista_sem_duplicatas = list(set(lista_imagens))
        lista_imagens_str = ", ".join(lista_sem_duplicatas)
         
        # Cria o DataFrame imagem
        if len(lista_sem_duplicatas) >0:
            df_imagens = pd.DataFrame(lista_sem_duplicatas)
            df_imagens = df_imagens.transpose()
            df_imagens.columns = [f'Imagem {i+1}' for i in range(len(df_imagens.columns))]
        else:
            df_imagens =""
        # Captura todos os <p> que vêm depois do elemento com data-store contendo 'product-description-'
        paragraphs = page.query_selector_all('//*[@id="descricao"]/p')
        if len(paragraphs) == 0:
            paragraphs = page.query_selector_all('//*[@id="descricao"]')
        # Usa lambda para extrair os textos dos <p> encontrados
        paragraph_texts = list(map(lambda p: p.inner_text(), paragraphs))
        
        lista_limpa = [item.replace('\n', ' ').strip() for item in paragraph_texts]
        description = " ".join([item for item in lista_limpa if item.strip()])         
        
        # Extraindo MEDIDA (por exemplo, "16cm")
        match_medida = re.search(r"MEDIDA:\s*([\d,]+cm)", description)
        tamanho = match_medida.group(1) if match_medida else "15"
        tamanho = tamanho.replace('cm','')

        match_peso = re.search(r"PESO:\s*([\d,]+g)", description)
        peso = match_peso.group(1) if match_peso else ".0019"
        peso = float(peso.replace('g','').replace(',','.'))/1000
        
        return [df_imagens,{
            'ID': codigo,
            'Preço promocional': 0,
            "Tipo": "simple",
            "GTIN UPC EAN ISBN": "",
            'Nome': produto,
            "Publicado": 1,
            "Em Destaque": 0,
            "Visibilidade no Catálogo": "visible",
            "Descrição Curta": "",
            "Descrição": description,
            "Data de Preço Promocional Começa em": "",
            "Data de Preço Promocional Termina em": "",
            "Status do Imposto": "taxable",
            "Classe de Imposto": "",
            "Em Estoque": 20,
            "Estoque": 20,
            "Quantidade Baixa de Estoque": 3,
            "São Permitidas Encomendas": 0,
            "Vendido Individualmente": 0,
            "Peso (kg)": peso,
            "Comprimento (cm)": tamanho,
            "Largura (cm)": "",
            "Altura (cm)": "",
            "Permitir avaliações de clientes?": 1,
            "Nota de Compra": "",
            "Preço Promocional": "",
            "Preço de Custo": preco_str,
            "Preço de Venda": preco_venda,
            "Categorias": categoria,
            "Tags": "",
            "Classe de Entrega": "",
            "Imagens": lista_imagens_str,
            "Limite de Downloads": "",
            "Dias para Expirar o Download": "",
            "Ascendente": f"id:{codigo}",
            "Grupo de Produtos": "",
            "Upsells": "",
            "Venda Cruzada": "",
            "URL Externa": "",
            "Texto do Botão": "",
            "Posição": 0,
            "Brands": "",
            "Nome do Atributo 1": "",
            "Valores do Atributo 1": "",
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": "",
            "Atributo Padrão 1": "",
            "Nome do Atributo 2": "",
            "Valores do Atributo 2": "",
            "Visibilidade do Atributo 2": 0,
            "Atributo Global 2": "",
            "Atributo Padrão 2": "",
            "Galpão": " Galpão 5"
        }]


    except Exception as e:
        print(f"Erro ao extrair dados do produto: {e}")
        return None

# Função principal para realizar o scraping
def scrape_florattajoias(base_url):
    products_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o navegador em ação
        page = browser.new_page()
        page.goto(base_url)
        cont = 0
        products_data = []        
        categorias = page.query_selector_all('(//*[@class="elemento-responsivo"])[4]//a')
        urls = list(map(lambda link: link.get_attribute('href'), categorias))
        urls_categoria =[href for href in urls if href and re.search(r'\d$', href)]
        #urls_categoria.insert(0, categoria_ofertas)
        for url_categoria in urls_categoria:
            page.goto(f"{base_url}{url_categoria}")
            time.sleep(.5)
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(.5)
                product_links = page.query_selector_all('//*[@id="ulListaProdutos"]/li/a')
                product_urls = list(map(lambda link: link.get_attribute('href'), product_links))
            except:
                continue

            for url_product in product_urls:
        
                page.goto(f"{base_url}{url_product}")
                time.sleep(2)   
                product_data = extract_product_data(page)
                df_imagens = product_data[0]
                df_produto = pd.DataFrame([product_data[1]])     
                         
                if len(df_imagens) >0:
                    df_produto = pd.concat([df_produto, df_imagens], axis=1)

                df_final = df_produto
                products_data.append(df_final)
                df_final = pd.concat(products_data, ignore_index=True)
                df_final = df_final.fillna("")
                cont = cont + 1
                if cont >= 1:
                    time.sleep(.3)
                    save_to_sheets(df_final)
                    time.sleep(.3)
                    cont = 0
        browser.close()

        return df_final