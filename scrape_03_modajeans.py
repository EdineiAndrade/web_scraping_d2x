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
    save_to_google_sheets(data,2)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page, url_product,nome_categiria):
    try:
        page.goto(url_product)
        time.sleep(1)
        # Extrair informações usando os seletores fornecidos
        produto = url_product.split('/')[-2].replace('-',' ').title()
        titulo = page.locator('//*[@class="page-header  "]//h1').inner_text().replace('SKU - ','')
        sku = next(iter(re.findall(r'\d+', titulo)), '0')
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
        variavel_cor_tamanho = page.locator('(//*[@id="product_form"]/div//label)[1]').inner_text()
        try:
                #variação de cor
            if "Cor" in variavel_cor_tamanho:
                variacao_cor = page.query_selector_all('(//*[@id="product_form"]/div/div)[1]/a')
                lista_cores = list(map(lambda cor: {
                    "Valores do Atributo 2": cor.get_attribute("title"),
                    "Estoque": 0 if "btn-variant-no-stock" in cor.get_attribute("class") else 1
                }, variacao_cor)) 
                cores = [item['Valores do Atributo 2'] for item in lista_cores]
                cores_str = ", ".join(cores)
                df_cores = pd.DataFrame(lista_cores)
                cor = "Cor Personalizada"
                atributo_global_2 = 1
                cor_padrao = cores[0]
            else:
                atributo_global_2 = df_cores = cor_padrao = cores_str = cor = ""
        except Exception as e:
            print(f"Erro ao extrair dados do produto: {e}")
            df_cores = cor_padrao = cores_str = cor = ""
        # Seleciona todas as LABELS com data-qty="0" dentro das divs de opção
        if "Tamanho" in variavel_cor_tamanho:
            label_tamanho = page.query_selector_all('(//*[@id="product_form"]/div/div)[1]/a')
        else:
            label_tamanho = page.query_selector_all('//*[@id="product_form"]/div/div[2]//a')    
        list_tamanhos = list(map(lambda t: {
            "Valores do Atributo 1": t.get_attribute("title"),
            "Estoque": 0 if "btn-variant-no-stock" in t.get_attribute("class") else 1
        }, label_tamanho)) 

        tamanhos = [item['Valores do Atributo 1'] for item in list_tamanhos]
        if tamanhos[0] == 'Único (36 ao 42)':
                list_tamanhos = list(map(lambda tamanho: {
                    "Valores do Atributo 1": tamanho, 
                    "Estoque": 1
                }, range(36, 43)))
                tamanhos = [item['Valores do Atributo 1'] for item in list_tamanhos]
                tamanhos_str = ", ".join(map(str, tamanhos))
        else:
            tamanhos_str = ", ".join(tamanhos)
        
        df_tamanhos = pd.DataFrame(list_tamanhos)
        df_tamanhos["Valores do Atributo 1"] = df_tamanhos["Valores do Atributo 1"].astype(str)
        tamanho_meio = tamanhos_str.split(",")[int(len(tamanhos_str.split(","))/2)-1].replace("'","").replace('"','').replace(' ','')
    
        return [df_tamanhos,df_cores,{
            'ID': codigo,
            'SKU':sku,
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
            "Valores do Atributo 1": tamanhos_str,
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": 1,
            "Atributo Padrão 1": tamanho_meio,
            "Nome do Atributo 2": cor,
            "Valores do Atributo 2": cores_str,
            "Visibilidade do Atributo 2": 0,
            "Atributo Global 2": atributo_global_2,
            "Atributo Padrão 2": cor_padrao
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
            #url_product = 'https://atacadodamodajeans.lojavirtualnuvem.com.br/produtos/short-jeans-com-barra-desfiada/'
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
                df_cores = product_data[1]
                df_produto = pd.DataFrame([product_data[2]])                
                # Explodir a coluna "Valores do Atributo 1"
                if len(df_cores) <= 1: 
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
                else:
                    coluna_atributo = "Valores do Atributo 2"
                    df_explodido = df_produto.explode(coluna_atributo).reset_index(drop=True)
                    df_explodido[coluna_atributo] = df_explodido[coluna_atributo].str.split(", ")
                    df_explodido = df_explodido.explode(coluna_atributo, ignore_index=True)
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
                df_ref = df_tamanhos if coluna_atributo == "Valores do Atributo 1" else df_cores
                df_final = df_explodido.merge(
                    df_ref[[coluna_atributo, "Estoque"]],
                    on=coluna_atributo,
                    how="left"
                )
                df_final["Em Estoque"] = df_final["Estoque"]     
                df_final = pd.concat([df_produto, df_final], ignore_index=True)
                products_data.append(df_final)
                df_final = pd.concat(products_data, ignore_index=True)
                df_final = df_final.fillna("")
                cont = cont + 1
                if cont >= 20:
                    time.sleep(1)
                    save_to_sheets(df_final)
                    time.sleep(1)
                    cont = 0
        browser.close()

        return df_final