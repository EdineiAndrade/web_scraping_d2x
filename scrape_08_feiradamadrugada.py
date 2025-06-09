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
    save_to_google_sheets(data,7)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page, url_product,nome_categiria):
    try:
        #page.goto(url_product)
        time.sleep(.5)
        # Extrair informações usando os seletores fornecidos
        produto = url_product.split('/')[-2].replace('-',' ').title()
        titulo = page.locator('//*[@class="fr col-sm-5 col-xs-12 product-detail"]/div/h1').inner_text()
        codigo = url_product.split('/')[-1].replace('-','').replace(' ','')
        categoria = nome_categiria.title()
        print(f"Processando categoria: {categoria} | produto:{produto}")
        preco = page.locator('//*[@id="content_product"]/div/div/div[2]/div[2]/form/div[2]/div[1]/div[1]/meta[3]').get_attribute('content')
        preco_custo = str(round(float(preco.replace(',', '.')), 2))
        preco_venda = str(round(float(preco_custo)* 1.1,2))
        imagem = page.query_selector_all('//*[@id="sly_carousel"]/ul/li/a')
        lista_imagens = list(map(lambda link: "https:" + link.get_attribute('big_img')
                         if link.get_attribute('big_img') else "", imagem))
        lista_sem_duplicatas = list(set(lista_imagens))
        lista_imagens = ", ".join(lista_sem_duplicatas)
         
         # Cria o DataFrame imagem
        if len(lista_sem_duplicatas) >0:
            df_imagens = pd.DataFrame(lista_sem_duplicatas)
            df_imagens = df_imagens.transpose()
            df_imagens.columns = [f'Imagem {i+1}' for i in range(len(df_imagens.columns))]
        else:
            df_imagens =""

        # Captura todos os <p> que vêm depois do elemento com data-store contendo 'product-description-'
        paragraphs = page.query_selector_all('(//*[@class="float"])[7]//p')
        # Usa lambda para extrair os textos dos <p> encontrados
        paragraph_texts = list(map(lambda p: p.inner_text(), paragraphs))
        lista_limpa = [item.replace('\xa0', ' ').strip() for item in paragraph_texts]
        description = " ".join([item for item in lista_limpa if item.strip()])
        variavel_cor = page.locator('//*[@id="grade"]/div/div/div/div[1]/div[1]').inner_text().title()
        variavel_tamanho = page.locator('//*[@id="grade"]/div/div/div/div[2]/div[1]').inner_text().title()
        try:
                #variação de cor
            if "Cor" in variavel_cor:
                variacao_cor = page.query_selector_all('//*[@class="filter_lists"]/div[1]//img')
                lista_cores = list(map(lambda cor: {
                    "Valores do Atributo 2": cor.get_attribute("title"), "Estoque":10}, variacao_cor)) 
                cores = [item['Valores do Atributo 2'] for item in lista_cores]
                cores_str = ", ".join(cores)
                df_cores = pd.DataFrame(lista_cores)
                cor = "Cor"
                atributo_global_2 = 1
                cor_padrao = cores[0]
            else:
                atributo_global_2 = df_cores = cor_padrao = cores_str = cor = ""
        except Exception as e:
            print(f"Erro ao extrair dados do produto: {e}")
            df_cores = cor_padrao = cores_str = cor = ""
        # Seleciona todas as LABELS com data-qty="0" dentro das divs de opção
        if "Tamanho" in variavel_tamanho:
            label_tamanho = page.query_selector_all('//*[@class="float required group tam"]//span')
        else:
            label_tamanho = page.query_selector_all('//*[@id="product_form"]/div/div[2]//a')    
        
        if label_tamanho:
            list_tamanhos = list(map(lambda t: {
                "Valores do Atributo 1": t.inner_text().strip().replace('\n', '').replace('\t', '').replace(' ', ''), "Estoque":10}, label_tamanho)) 

            tamanhos = [item['Valores do Atributo 1'] for item in list_tamanhos]
            tamanhos_str = ", ".join(tamanhos)        
            df_tamanhos = pd.DataFrame(list_tamanhos)
            df_tamanhos["Valores do Atributo 1"] = df_tamanhos["Valores do Atributo 1"].astype(str)
            tamanho_meio = tamanhos_str.split(",")[int(len(tamanhos_str.split(","))/2)-1].replace("'","").replace('"','').replace(' ','')
            atributo1 = "Tamanho"
            if len(df_tamanhos) <=0:
               atributo1 = tamanho_meio = tamanhos_str = df_tamanhos = " "
        else:
            atributo1 = tamanho_meio = tamanhos_str = df_tamanhos = " "
        if df_cores is None:
                df_cores = [] 
        if df_tamanhos is None:
            f_cores = []
        return [df_tamanhos,df_cores,df_imagens,{
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
            "Preço de Custo": preco_custo,
            "Preço de Venda": preco_venda,
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
            "Nome do Atributo 1": atributo1,
            "Valores do Atributo 1": tamanhos_str,
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": 1,
            "Atributo Padrão 1": tamanho_meio,
            "Nome do Atributo 2": cor,
            "Valores do Atributo 2": cores_str,
            "Visibilidade do Atributo 2": 0,
            "Atributo Global 2": atributo_global_2,
            "Atributo Padrão 2": cor_padrao,
            "Galpão": " Galpão 3"
        }]


    except Exception as e:
        print(f"Erro ao extrair dados do produto: {e}")
        return None

# Função principal para realizar o scraping
def scrape_08_feiram(base_url):
    products_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o navegador em ação
        page = browser.new_page()
        page.goto(base_url)
        cont = 0
        products_data = []
        # Definição do caminho do arquivo
        categorias = page.query_selector_all('(//*[@class="all-departments child level-0 first"])[1]/div/ul/li/a')
        urls_categoria = list(map(lambda link: link.get_attribute('href'), categorias))
        for url_categoria in urls_categoria:
            nome_categiria = url_categoria.replace('/','').title()
            page.goto(f"{base_url}/{url_categoria}") 
            
            texto = page.text_content("li.info")
            # Expressão regular para capturar o último número
            match = re.search(r'Página\s+\d+\s+de\s+(\d+)', texto)

            if match:
                total_paginas = int(match.group(1))
                print(total_paginas)  
            else:
                total_paginas = 1
            # Calcular o número total de produtos
            for i in range(1, total_paginas + 1):
                page.goto(f"{base_url}/{url_categoria}?p={i}")
                try:    
                    product_links = page.query_selector_all('//*[contains(@class, "list-products") and contains(@class, "page-content")]/li/div/a[1]') 
                    product_urls = list(map(lambda link: link.get_attribute('href'), product_links))
                except:
                    continue  
                for url_product in product_urls:    
                    url_product = 'bre-01/p/221026/'
                    page.goto(f"{base_url}/{url_product}")
                    time.sleep(.5)                    
                    product_data = extract_product_data(page, url_product,nome_categiria)    
                    df_tamanhos = product_data[0]          
                    df_cores = product_data[1]
                    df_imagens = product_data[2]               
                    df_produto = pd.DataFrame([product_data[3]])    

                    if len(df_imagens) >0:
                        df_produto = pd.concat([df_produto, df_imagens], axis=1)           
                    # Explodir a coluna "Valores do Atributo 1"
                    if len(df_cores) <= 1 and len(df_tamanhos)>1: 
                        coluna_atributo = "Valores do Atributo 1"
                        df_explodido = df_produto.explode(coluna_atributo).reset_index(drop=True) 
                        if df_explodido[coluna_atributo].apply(lambda x: any(item in {'P', 'M', 'G', 'GG'} for item in x)).any():
                            df_explodido[coluna_atributo] = df_explodido[coluna_atributo].apply(
                                lambda x: x.split(", ") if x == "P, M, G, GG" else x
                            )
                        else:
                            df_explodido[coluna_atributo] = df_explodido[coluna_atributo].apply(
                            lambda x: ast.literal_eval(x)
                        )
                        df_explodido = df_explodido.explode(coluna_atributo).reset_index(drop=True)
                        
                    elif len(df_cores) <= 1 and len(df_tamanhos)<=1:

                        df_explodido = df_produto.explode("Valores do Atributo 1").reset_index(drop=True)
                    
                    else:
                        coluna_atributo = "Valores do Atributo 2"
                        df_explodido = df_produto.explode(coluna_atributo).reset_index(drop=True)
                        df_explodido[coluna_atributo] = df_explodido[coluna_atributo].str.split(", ")
                        df_explodido = df_explodido.explode(coluna_atributo, ignore_index=True)
                                            
                    df_explodido = df_explodido.drop(columns=["Estoque"])
                    if len(df_imagens) > 0:
                            numero_imagens = df_imagens.shape[1]
                            df_explodido.iloc[:, -numero_imagens:] = ""
                    df_explodido["Tipo"] = "variation"  
                    df_explodido[
                            ["Descrição","Peso (kg)","Comprimento (cm)","Largura (cm)",
                            "Altura (cm)","Categorias","Visibilidade do Atributo 1","Atributo Padrão 1",
                            "Quantidade Baixa de Estoque","Imagens"]
                                        ] = None
                    df_produto[
                                ["Classe de Imposto","Ascendente","Preço de Custo","Preço de Venda"]
                                    ] = None
                    df_explodido["Permitir avaliações de clientes?"] = 0
                    df_explodido["Posição"] = df_explodido.index + 1
                    df_explodido["ID"] = df_explodido["ID"].astype(str) + df_explodido["Posição"].astype(str)
                    
                    if len(df_cores) <= 1 and len(df_tamanhos)<=1:
                        df_final = df_produto 
                        pd.set_option('future.no_silent_downcasting', True)                   
                        df_final = df_final.fillna("").astype(str)
                        df_final["Tipo"] = "simple"   
                    else:
                        df_ref = df_tamanhos if coluna_atributo == "Valores do Atributo 1" else df_cores
                        df_final = df_explodido.merge(
                                df_ref[[coluna_atributo, "Estoque"]],
                                on=coluna_atributo,
                                how="left"
                            )
                        pd.set_option('future.no_silent_downcasting', True)
                        df_final = df_final.fillna("").astype(str)
                        df_final["Em Estoque"] = df_final["Estoque"]     
                        df_final["Tipo"] = "variation"
                        df_final = pd.concat([df_produto, df_final], ignore_index=True)
                    
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