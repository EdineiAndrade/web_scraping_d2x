from sheets import save_to_google_sheets
from playwright.sync_api import sync_playwright,TimeoutError
import pandas as pd
import time
import re

# Função para salvar os dados em um arquivo Excel
def save_to_sheets(data):    
    #data.to_excel(filename, index=False)
    save_to_google_sheets(data,5)
# Função para extrair dados de um produto na página de detalhes
def extract_product_data(page,product_id):
    try:
        # Extrair informações usando os seletores fornecidos
        time.sleep(.5)
        nome_categiria = page.locator('//*[@class="woocommerce-breadcrumb"]/a[2]').inner_text().title()
        produto = page.locator('//*[contains(@class, "product_title")]').inner_text().title()
        print(f"Processando categoria: {nome_categiria} | produto: {produto}")
        em_estoque = page.locator('//div[3]/section[1]/div[2]/div[2]/div/div[4]/div/p/b').inner_text()
        if em_estoque == "Fora de estoque":
            estoque,e_estoque = "0"
        else:
            estoque, e_estoque = "20","1"
        codigo = product_id

        try:
            sku = page.locator('//div[3]/section[1]/div[2]/div[2]/div/div[5]/div/h2').inner_text(timeout=100).replace('SKU: ', '')
        except:
            sku = ""
        try:
            ean = page.locator('//div[3]/section[1]/div[2]/div[2]/div/div[6]/div/h2').inner_text(timeout=100).replace('EAN: ','')
        except:
            ean = ""    
        try:
            ncm = page.locator('//div[3]/section[1]/div[2]/div[2]/div/div[7]/div/h2').inner_text(timeout=100).replace('NCM: ','')
        except:
            ncm = "" 
        
        preco_str = page.locator('(//*[@class="woocommerce-Price-amount amount"]/bdi)[1]').inner_text().replace('R$','').replace('.','').replace(',','.')
        preco_venda = str(round(float(preco_str)* 1.1,2))
        imagem = page.query_selector_all('//*[@class="woocommerce-product-gallery__wrapper"]//a')
        lista_imagens = list(map(lambda link: link.get_attribute('href'), imagem))     
        lista_sem_duplicatas = list(set(lista_imagens))
        lista_imagens_str = ", ".join(lista_sem_duplicatas)
         
        # Cria o DataFrame imagem
        if len(lista_sem_duplicatas) >0:
            df_imagens = pd.DataFrame(lista_sem_duplicatas)
            df_imagens = df_imagens.transpose()
            df_imagens.columns = [f'Imagem {i+1}' for i in range(len(df_imagens.columns))]
        else:
            df_imagens =""
        #df cores    
        try:
            variavel_cor = page.locator('//div[3]/section[1]/div[2]/div[2]/div/div[12]/div/div/form/table/tbody/tr[2]/th/label').inner_text(timeout=200)
                #variação de cor
            if "COR" in variavel_cor.upper():
                variacao_cor = page.query_selector_all('(//*[@class="sps-swatches"])[2]/span')
                lista_cores = list(map(lambda cor:cor.get_attribute("data-value"), variacao_cor))
                cores_str = ", ".join(lista_cores)
                #df_cores = pd.DataFrame(lista_cores, columns=["Valores do Atributo 2"])
                cor = "Cor Personalizada"
                atributo_global_1 = 1
                cor_padrao = lista_cores[0]
            else:
                atributo_global_1 = cor_padrao = cores_str = cor = ""
        except Exception as e:
            print(f"Tipo de Produto: simple")
            atributo_global_1 = cor_padrao = cores_str = cor = ""

        # Captura todos os <p> que vêm depois do elemento com data-store contendo 'product-description-'
        paragraphs = page.query_selector_all('//*[@id="tab-description"]//p')
        # Usa lambda para extrair os textos dos <p> encontrados
        paragraph_texts = list(map(lambda p: p.inner_text(), paragraphs))
        
        lista_limpa = [item.replace('\n', ' ').strip() for item in paragraph_texts]
        description = " ".join([item for item in lista_limpa if item.strip()])         

        try:
            description_html = page.locator('//div[3]/section[2]/div[2]').inner_html(timeout=100)
            description_html = description_html.replace('\t', ' ').replace('\n', '<br>')
        except Exception as e:
            print(f"Erro ao extrair dados do produto: {e}")
            description_html = ""
        
        try:
            peso = page.locator('//div[3]/section[2]/div[2]/div/div/section/div[2]/div/div/div[1]/div/div/div[2]/table/tbody/tr[1]/td').inner_text(timeout=200)
            peso = str(peso.replace(' kg','').replace(',','.'))
        except:
            peso = "0.11"

        try:
            dimensoes = page.locator('//div[3]/section[2]/div[2]/div/div/section/div[2]/div/div/div[1]/div/div/div[2]/table/tbody/tr[2]/td').inner_text(timeout=200)
            regex = r'(\d+)\s×\s(\d+)\s×\s(\d+)\scm'
            resultado = re.match(regex, dimensoes)
            largura, comprimento, altura,cm = resultado.group(1),resultado.group(2),resultado.group(3),dimensoes[-2:]
        except:
            largura, comprimento, altura = "5","15","5"
        if cm != 'cm':
            largura, comprimento, altura = ""
        
        return [df_imagens,{
            'ID': codigo,
            "SKU":sku,
            "EAN": ean,
            "NCM":ncm,
            'Preço promocional': 0,
            "Tipo": "variable",
            'Nome': produto,
            "Publicado": 1,
            "Em Destaque": 0,
            "Visibilidade no Catálogo": "visible",
            "Descrição Curta": "",
            "Descrição": description,
            "Descrição html": description_html,
            "Data de Preço Promocional Começa em": "",
            "Data de Preço Promocional Termina em": "",
            "Status do Imposto": "taxable",
            "Classe de Imposto": "",
            "Em Estoque": e_estoque,
            "Estoque": estoque,
            "Quantidade Baixa de Estoque": 3,
            "São Permitidas Encomendas": 0,
            "Vendido Individualmente": 0,
            "Peso (kg)": peso,
            "Comprimento (cm)": comprimento,
            "Largura (cm)": largura,
            "Altura (cm)": altura,
           "Permitir avaliações de clientes?": 1,
            "Nota de Compra": "",
            "Preço Promocional": "",
            "Preço de Custo": preco_str,
            "Preço de Venda": preco_venda,
            "Categorias": nome_categiria,
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
            "Nome do Atributo 1": cor,
            "Valores do Atributo 1": cores_str,
            "Visibilidade do Atributo 1": 0,
            "Atributo Global 1": atributo_global_1,
            "Atributo Padrão 1": cor_padrao,
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
def scrape_06_cemstoretec(base_url):
    products_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para ver o navegador em ação
        page = browser.new_page()
        page.goto(base_url,timeout=100*10000)
        cont = 0
        products_data = []        
        categorias = page.query_selector_all("a.elementor-item")
        urls = list(map(lambda link: link.get_attribute('href'), categorias))
        urls_categoria = list(set(urls[:48]))
    
        for url_categoria in urls_categoria:
            page.goto(f"{url_categoria}")
            time.sleep(.5)

            try:
                # Aguarda até 200 milissegundos para que o seletor apareça
                page.wait_for_selector('//*[@class="jet-filters-pagination"]/div', timeout=1000)
                numero_pagina = len(page.query_selector_all('//*[@class="jet-filters-pagination"]/div'))
            except TimeoutError:
                numero_pagina = 2
            for pagina in range(1,numero_pagina):
                if pagina > 1:
                    page.goto(f'{url_categoria}?jsf=jet-woo-products-grid&tax=product_cat:154&pagenum={pagina}')
                try:
                    #page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(.5)

                    product_id = page.query_selector_all('//*[contains(@class,"jet-woo-products__item ")]')
                    product_ids = list(map(lambda link: link.get_attribute('data-product-id'), product_id))

                    product_links = page.query_selector_all('//*[@class="jet-woo-products jet-woo-products--preset-4 col-row  jet-equal-cols"]/div/a')
                    product_urls = list(map(lambda link: link.get_attribute('href'), product_links))
                except:
                    continue
                for product_id, url_product in zip(product_ids,product_urls):
            
                    page.goto(f"{url_product}")
                    time.sleep(.5)   
                    product_data = extract_product_data(page, product_id)
                    df_imagens = product_data[0]
                    df_produto = pd.DataFrame([product_data[1]])     
                            
                    if len(df_imagens) >0:
                        df_produto = pd.concat([df_produto, df_imagens], axis=1)

                    if df_produto["Valores do Atributo 1"].str.contains(',').any():
                        df_explodido = df_produto.explode("Valores do Atributo 1").reset_index(drop=True)
                        df_explodido["Valores do Atributo 1"] = df_explodido["Valores do Atributo 1"].str.split(", ")
                        df_explodido = df_explodido.explode("Valores do Atributo 1", ignore_index=True)  
                        df_explodido = df_explodido.drop(columns=["Estoque"])
                        df_explodido["Tipo"] = "variation"  
                        df_explodido[
                            ["Descrição","Peso (kg)","Comprimento (cm)","Largura (cm)",
                            "Altura (cm)","Categorias","Visibilidade do Atributo 1","Atributo Padrão 1",
                            "Quantidade Baixa de Estoque","Imagens","Estoque"]
                                    ] = ""                                 
                        df_produto[
                                ["Classe de Imposto","Ascendente","Preço de Custo","Preço de Venda"]
                                    ] = ""
                        df_explodido["Permitir avaliações de clientes?"] = 0
                        df_explodido["Posição"] = df_explodido.index + 1
                        df_explodido["ID"] = df_explodido["ID"].astype(str) + df_explodido["Posição"].astype(str)
                        #merge                                
                        if len(df_imagens) > 0:
                            numero_imagens = df_imagens.shape[1]
                            df_explodido.iloc[:, -numero_imagens:] = ""
                        df_final = pd.concat([df_produto, df_explodido], ignore_index=True)
                    else:
                        df_final = df_produto
                        df_final["Tipo"] = "simple" 
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