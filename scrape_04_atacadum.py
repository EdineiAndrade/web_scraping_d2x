from sheets import save_to_google_sheets
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import re

# Função para salvar os dados em um arquivo Excel
def save_to_sheets(data):    
    #data.to_excel(filename, index=False)
    save_to_google_sheets(data,3)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page,nome_categiria):
    try:
        #page.goto(url_product)
        time.sleep(2)
        # Extrair informações usando os seletores fornecidos
        produto = page.locator('//*[@class="detalhes"]/h3').inner_text().title()
        sku = page.locator('//*[@id="inc_sku"]/meta').get_attribute('content')
        categoria = nome_categiria.title()
        print(f"Processando categoria: {categoria} | produto:{produto}")
        try:
            marca = page.locator('(//*[@class="codigo_produto"]/span)[2]').inner_text(timeout=200)
        except:
            marca = ""
        codigo = page.locator('(//*[@class="codigo_produto"]/span)[1]').inner_text().replace('Cód.: ','')
        codigo = int("".join(re.findall(r'\d+', codigo)))
        preco = page.locator('//*[@class="valor"]/span[1]').inner_text().replace('R$','')
        imagem = page.query_selector_all('//*[@class="slick-track"]/div/img')
        lista_imagens = list(map(lambda link: link.get_attribute('src'), imagem))     
        lista_sem_duplicatas = list(set(lista_imagens))
        lista_imagens = ", ".join(lista_sem_duplicatas)
         
        # Captura todos os <p> que vêm depois do elemento com data-store contendo 'product-description-'
        paragraphs = page.query_selector_all('//*[@class="descricao"]/div//p')
        # Usa lambda para extrair os textos dos <p> encontrados
        paragraph_texts = list(map(lambda p: p.inner_text(), paragraphs))
        lista_limpa = [item.replace('\n', ' ').strip() for item in paragraph_texts]
        description = " ".join([item for item in lista_limpa if item.strip()])
        variavel_cor = page.locator('//*[@class="cores"]/div[1]').inner_text()
        try:
                #variação de cor
            if "COR" in variavel_cor:
                variacao_cor = page.query_selector_all('//*[@class="cores"]/div[2]/div')
                lista_cores = list(map(lambda cor:cor.get_attribute("data-original-title"), variacao_cor))
                cores_str = ", ".join(lista_cores)
                #df_cores = pd.DataFrame(lista_cores, columns=["Valores do Atributo 2"])
                cor = "Cor Personalizada"
                atributo_global_1 = 1
                cor_padrao = lista_cores[0]
            else:
                atributo_global_1 = cor_padrao = cores_str = cor = ""
        except Exception as e:
            print(f"Erro ao extrair dados do produto: {e}")
            atributo_global_1 = cor_padrao = cores_str = cor = ""        
        
        return {
            'ID': codigo,
            'SKU':sku,
            'Preço promocional': 0,
            "Tipo": "variable",
            "GTIN UPC EAN ISBN": "",
            'Nome': produto,
            'Marca': marca,
            "Publicado": 1,
            "Em Destaque": 0,
            "Visibilidade no Catálogo": "visible",
            "Descrição Curta": "",
            "Descrição": description,
            "Data de Preço Promocional Começa em": "",
            "Data de Preço Promocional Termina em": "",
            "Status do Imposto": "taxable",
            "Classe de Imposto": "parent",
            "Em Estoque": 1,
            "Estoque": 1,
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
            "Nome do Atributo 1": cor,
            "Valores do Atributo 1": cores_str,
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": atributo_global_1,
            "Atributo Padrão 1": cor_padrao,
            "Nome do Atributo 2": "",
            "Valores do Atributo 2": "",
            "Visibilidade do Atributo 2": 0,
            "Atributo Global 2": "",
            "Atributo Padrão 2": ""
        }


    except Exception as e:
        print(f"Erro ao extrair dados do produto: {e}")
        return None

# Função principal para realizar o scraping
def scrape_atacadum(base_url):
    products_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o navegador em ação
        page = browser.new_page()
        page.goto(base_url)
        cont = 0
        products_data = []
        # Definição do caminho do arquivo
        categoria_ofertas = page.locator('(//*[@class="categorias_desk"]/li/a)[1]').get_attribute('href')
        categorias = page.query_selector_all('//*[@class="categorias_desk"]/li/div/ul/li/a')
        urls_categoria = list(map(lambda link: link.get_attribute('href'), categorias))
        urls_categoria.insert(0, categoria_ofertas)
        for url_categoria in urls_categoria:
            nome_categiria = url_categoria[:-1].replace('/','>').replace('-',' ').title()
            page.goto(f"{base_url}{url_categoria}")
            time.sleep(1)
            try:    
                product_links = page.query_selector_all('//*[@class="produtos"]/div/div/div/a') 
                product_urls = list(map(lambda link: link.get_attribute('href'), product_links))
            except:
                continue

            for url_product in product_urls:
                #url_product = 'smartwatch-n9-pro-serie-10-47mm-pulseira-extra-lancamento/'
                page.goto(f"{base_url}{url_product}")
                time.sleep(2)                
                product_data = extract_product_data(page,nome_categiria)
            
                df_produto = pd.DataFrame([product_data])                
                
                df_explodido = df_produto.explode("Valores do Atributo 1").reset_index(drop=True)
                df_explodido["Valores do Atributo 1"] = df_explodido["Valores do Atributo 1"].str.split(", ")
                df_explodido = df_explodido.explode("Valores do Atributo 1", ignore_index=True)  
                df_explodido = df_explodido.drop(columns=["Estoque"])
                df_explodido["Tipo"] = "variation"  
                df_explodido[
                    ["Descrição","Peso (kg)","Comprimento (cm)","Largura (cm)",
                     "Altura (cm)","Categorias","Visibilidade do Atributo 1","Atributo Padrão 1",
                     "Quantidade Baixa de Estoque","Imagens"]
                                 ] = None                                 
                df_produto[
                        ["Classe de Imposto","Ascendente","Preço"]
                               ] = None
                df_explodido["Permitir avaliações de clientes?"] = 0
                df_explodido["Posição"] = df_explodido.index + 1
                df_explodido["ID"] = df_explodido["ID"].astype(str) + df_explodido["Posição"].astype(str)
                #merge                                
                   
                df_final = pd.concat([df_produto, df_explodido], ignore_index=True)
                products_data.append(df_final)
                df_final = pd.concat(products_data, ignore_index=True)
                df_final = df_final.fillna("")
                cont = cont + 1
                if cont >= 20:
                    time.sleep(.3)
                    save_to_sheets(df_final)
                    time.sleep(.3)
                    cont = 0
        browser.close()

        return df_final