from sheets import save_to_google_sheets
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re
import math
import ast

# Função para salvar os dados em um arquivo Excel
def save_to_sheets(data):    
    #data.to_excel(filename, index=False)
    save_to_google_sheets(data,3)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page, url_product,nome_categiria):
    try:
        page.goto(url_product)
        time.sleep(1)
        # Extrair informações usando os seletores fornecidos
        produto = url_product.split('/')[-2].replace('-',' ').title()
        sku = page.locator('//*[@class="page-header  "]//h1').inner_text().replace('SKU - ','')
        categoria = nome_categiria.title()
        print(f"Processando categoria: {categoria} | produto:{produto}")
        codigo = page.locator('//*[@class="page-header  "]//h1').get_attribute('data-store').replace('product-name-','')
        preco = page.locator('//*[@id="price_display"]').inner_text().replace('R$','')
        imagem = page.query_selector_all('//*[@class="swiper-wrapper"]//img')
        lista_imagens = list(map(lambda link: "https:" + link.get_attribute('srcset').split(',')[-1].split()[0] 
                         if link.get_attribute('srcset') else "", imagem))
        lista_filtrada = [item for item in lista_imagens if item and (not isinstance(item, float) or not math.isnan(item))]
        lista_filtrada = [link for link in lista_filtrada if "-1024-1024" in link]
        
        lista_sem_duplicatas = list(set(lista_filtrada))
        lista_imagens = ", ".join(lista_sem_duplicatas)
         
        # Captura todos os <p> que vêm depois do elemento com data-store contendo 'product-description-'
        paragraphs = page.query_selector_all('//*[@data-store[contains(., "product-description-")]]//p')
        # Usa lambda para extrair os textos dos <p> encontrados
        paragraph_texts = list(map(lambda p: p.inner_text(), paragraphs))
        lista_limpa = [item.replace('\xa0', ' ').strip() for item in paragraph_texts]
        description = " ".join([item for item in lista_limpa if item.strip()])
        # Seleciona todas as LABELS com data-qty="0" dentro das divs de opção
        label_tamanho = page.query_selector_all('//*[@id="product_form"]/div/div[2]//a')
        list_tamanhos = list(map(lambda t: {
            "Valores do Atributo 1": t.get_attribute("title"),
            "Estoque": 0 if "btn-variant-no-stock" in t.get_attribute("class") else 1
        }, label_tamanho))               
        tamanhos = [item['Valores do Atributo 1'] for item in list_tamanhos]
        tamanhos_str = ", ".join(tamanhos)
        df_tamanhos = pd.DataFrame(list_tamanhos)
        df_tamanhos["Valores do Atributo 1"] = df_tamanhos["Valores do Atributo 1"].astype(str)

        return [df_tamanhos,{
            'ID': codigo,
            'Preço promocional': 0,
            "Tipo": "variable",
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
            "Classe de Imposto": "parent",
            "Em Estoque": 0,
            "Estoque": "",
            "Quantidade Baixa de Estoque": 3,
            "São Permitidas Encomendas": 0,
            "Vendido Individualmente": 0,
            "Peso (kg)": 1,
            "Comprimento (cm)": 32,
            "Largura (cm)": 20,
            "Altura (cm)": 12,
            "Permitir avaliações de clientes?": 1,
            "Nota de Compra": "",
            "Preço Promocional": "",
            "Preço": preco,
            "Categorias": categoria,
            "Tags": "",
            "Classe de Entrega": "",
            "Imagens": lista_imagens,
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
            "Nome do Atributo 1": "Tamanho",
            "Valores do Atributo 1": tamanhos,
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": 1,
            "Atributo Padrão 1": tamanho_meio,
            "Nome do Atributo 2": "",
            "Valores do Atributo 2": "",
            "Visibilidade do Atributo 2": 0,
            "Atributo Global 2": "",
            "Atributo Padrão 2": ""
        }]


    except Exception as e:
        print(f"Erro ao extrair dados do produto: {e}")
        return None

# Função principal para realizar o scraping
def scrape_modajeans(base_url):
    products_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o navegador em ação
        page = browser.new_page()
        page.goto(base_url)
        cont = 0
        products_data = []
        # Definição do caminho do arquivo
        categorias = page.query_selector_all('//*[@class="js-accordion-container "]//li/a')
        urls_categoria = list(map(lambda link: link.get_attribute('href'), categorias))
        for url_categoria in urls_categoria:
            nome_categiria = url_categoria.split('/')[-2].title()
            page.goto(f"{url_categoria}?mpage=4") #?mpage=4
            time.sleep(1)
            try:    
                product_links = page.query_selector_all('//*[@class="js-item-product col-6 col-md-2-4 item-product col-grid is-inViewport"]/div[1]/div[1]/div[1]/div/a') 
                product_urls = list(map(lambda link: link.get_attribute('href'), product_links))
            except:
                continue

            for url_product in product_urls:               
                product_data = extract_product_data(page, url_product,nome_categiria)
                df_tamanhos = product_data[0]
                df_produto = pd.DataFrame([product_data[1]])
                df_produto["Valores do Atributo 1"] = df_produto["Valores do Atributo 1"].apply(
                    lambda x: ast.literal_eval(x)
                )
                # Explodir a coluna "Valores do Atributo 1"   
                df_explodido = df_produto.explode("Valores do Atributo 1").reset_index(drop=True)
                df_explodido = df_explodido.drop(columns=["Estoque"])
                df_explodido["Tipo"] = "variation"  
                df_explodido[
                    ["Descrição","Peso (kg)","Comprimento (cm)","Largura (cm)",
                     "Altura (cm)","Categorias","Visibilidade do atributo 1","Atributo Padrão 1",
                     "Quantidade Baixa de Estoque","Imagens"]
                                 ] = None
                df_produto[
                        ["Classe de Imposto","Ascendente","Preço"]
                               ] = None
                df_explodido["Permitir avaliações de clientes?"] = 0
                df_explodido["Posição"] = df_explodido.index + 1
                df_explodido["ID"] = df_explodido["ID"].astype(str) + df_explodido["Posição"].astype(str)
                df_final = df_explodido.merge(
                    df_tamanhos[["Valores do Atributo 1", "Estoque"]],  # Selecionar colunas desejadas
                    on="Valores do Atributo 1",
                    how="left"
                )
                df_final["Em Estoque"] = df_final["Estoque"]     
                df_final = pd.concat([df_produto, df_final], ignore_index=True)
                products_data.append(df_final)
                df_final = pd.concat(products_data, ignore_index=True)
                cont = cont + 1
                if cont >= 1:
                    time.sleep(1)
                    save_to_sheets(df_final)
                    time.sleep(1)
                    cont = 0
        browser.close()

        return df_final