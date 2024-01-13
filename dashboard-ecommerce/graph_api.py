import requests
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def get_facebook_insights(access_token, ad_account_id, start_date, end_date, include_revenue=False):
    base_url = "https://graph.facebook.com/v18.0/"
    endpoint = f"{ad_account_id}/insights"

    fields = "campaign_name,adset_name,ad_name,spend,clicks,impressions,actions,action_values"
 
    params = {
        "time_increment": 1,
        "level": "ad",
        "fields": fields,
        "filtering": "[{'field':'action_type','operator':'IN','value':['purchase', 'add_to_cart', 'landing_page_view', 'view_content']}]",
        "access_token": access_token,
    }

    data = []
    next_url = None

    while True:
        if next_url:
            response = requests.get(next_url)
        else:
            response = requests.get(base_url + endpoint, params=params)

        response_data = response.json()
        data.extend(response_data.get("data", []))

        if 'paging' in response_data and 'next' in response_data['paging']:
            next_url = response_data['paging']['next']
        else:
            break

    return {"data": data}

def transform_data(data):
    new_data = []
    for entry in data:
        
        actions = entry.get("actions", [])
        for action in actions:
            entry[action["action_type"]] = int(action["value"])

       
        action_values = entry.get("action_values", [])
        for action_value in action_values:
            entry[f"{action_value['action_type']}_value"] = float(action_value["value"])

        new_data.append(entry)
    return new_data

def main():
    st.set_page_config(layout="wide",initial_sidebar_state="collapsed")
    access_token = "COLOQUE O TOKEN DA API DO META ADS AQUI"
    ad_account_id = "act_ID DA CONTA DE ANUNCIO"
    start_date = "2023-12-24"
    end_date = "2024-01-07"

    data = get_facebook_insights(access_token, ad_account_id, start_date, end_date, include_revenue=False)
    transformed_data = transform_data(data["data"])

    df = pd.DataFrame(transformed_data)
    
    page_bg = '''
        <style>
        [data-testid="block-container"] {
            padding-top: 0;
            padding-bottom: 0;
        }
        [data-testid="stAppViewContainer"] {
            height: 1080px !important;
        }
        [data-testid="stHorizontalBlock"] {
            max-width: 1920px !important;
        }
        [data-testid="stVerticalBlock"] {
            max-height: 1080px !important;
        }
        [data-testid="stImage"] {
            padding-top: 350px;
            padding-left: 40px;
            opacity: 0.5;
        }
        [data-testid="stTable"]{
            padding-top: 50px;
        }
        </style>
    ''' 
    st.markdown(page_bg, unsafe_allow_html=True)    

    if 'actions' in df.columns:
        df.drop(columns=['actions'], inplace=True)  


    if 'action_values' in df.columns:
        df.drop(columns=['action_values'], inplace=True) 
    

    if 'add_to_cart' in df.columns and 'purchase' in df.columns:
        unique_campaigns = df['campaign_name'].unique()

        add_to_cart_list = []
        purchase_list = []
        landing_page_view_list = []
        view_content_list = []
        spend_list = []
        impressions_list = []
        purchases_list = []
        revenue_list = []


        for campaign in unique_campaigns:
            add_to_cart_sum = df[df['campaign_name'] == campaign]['add_to_cart'].sum()
            purchase_sum = df[df['campaign_name'] == campaign]['purchase'].sum()
            landing_page_view_sum = df[df['campaign_name'] == campaign]['landing_page_view'].sum()
            view_content_sum = df[df['campaign_name'] == campaign]['view_content'].sum()
            spend_sum = pd.to_numeric(df[df['campaign_name'] == campaign]['spend'], errors='coerce').sum()  # Convertendo para numérico
            impressions_sum = pd.to_numeric(df[df['campaign_name'] == campaign]['impressions'], errors='coerce').sum()  # Convertendo para numérico
            purchases_sum = pd.to_numeric(df[df['campaign_name'] == campaign]['purchase'], errors='coerce').sum()  # Convertendo para numérico
            revenue_sum = pd.to_numeric(df[df['campaign_name'] == campaign]['purchase_value'], errors='coerce').sum()  # Convertendo para numérico
            revenue_list.append(revenue_sum)
            purchases_list.append(purchases_sum)
            impressions_list.append(impressions_sum)
            add_to_cart_list.append(add_to_cart_sum)
            purchase_list.append(purchase_sum)
            landing_page_view_list.append(landing_page_view_sum)
            view_content_list.append(view_content_sum)
            spend_list.append(spend_sum)

        dfgraph1 = pd.DataFrame({
            "Adicionaram ao Carrinho": add_to_cart_list,
            "Compraram": purchase_list,
            "Campanhas": unique_campaigns
        })

        df_funnel = pd.DataFrame({
            "stage": ["Visualizações", "Entraram na Página", "Adicionaram ao Carrinho", "Compraram"],
            "value": [sum(view_content_list), sum(landing_page_view_list), sum(add_to_cart_list), sum(purchase_list)]
        })

        
        unique_adsets = df['adset_name'].unique()

        adset_purchase_list = []

        for adset in unique_adsets:
            purchase_sum = df[df['adset_name'] == adset]['purchase'].sum()
            adset_purchase_list.append(purchase_sum)




        end_date = datetime.now() - timedelta(days=1)
        start_date = pd.to_datetime(df['date_start'].iloc[0])

        
        st.sidebar.header("Seletor de Opções")


        select_option = st.sidebar.radio("Selecione uma opção:", ["Data de Início", "Campanha"])
        selected_value = None

        if select_option == "Data de Início":

            date_start = st.sidebar.date_input("Selecione a Data de Início:", value=start_date)
            

            date_end = st.sidebar.date_input("Selecione a Data de Término:", value=end_date)


            df['date_start'] = pd.to_datetime(df['date_start'])
            df['date_stop'] = pd.to_datetime(df['date_stop'])

            filtered_df = df[(df['date_start'] >= pd.to_datetime(date_start)) & (df['date_stop'] <= pd.to_datetime(date_end))].copy()
            title_text = f"Total de Add to Cart e Purchase para a Data de Início: {selected_value}"
        else:
           
            selected_value = st.sidebar.selectbox("Selecione a Campanha:", df['campaign_name'].unique())
            filtered_df = df[df['campaign_name'] == selected_value].copy()
            filtered_df['campaign_name'] = selected_value

            
            campaign_start_date = st.sidebar.date_input("Selecione a Data de Início da Campanha:", value=start_date)
            campaign_end_date = st.sidebar.date_input("Selecione a Data de Término da Campanha:", value=end_date)

           
            filtered_df['date_start'] = pd.to_datetime(filtered_df['date_start'])
            filtered_df['date_stop'] = pd.to_datetime(filtered_df['date_stop'])

            
            filtered_df = filtered_df[(filtered_df['date_start'] >= pd.to_datetime(campaign_start_date)) & (filtered_df['date_stop'] <= pd.to_datetime(campaign_end_date))].copy()
            
            title_text = f"Total de Add to Cart e Purchase para a Campanha: {selected_value}"

       
        dfgraph1 = pd.DataFrame({
            "Campanhas": filtered_df['campaign_name'],
            "Adicionaram ao Carrinho": filtered_df['add_to_cart'],
            "Compraram": filtered_df['purchase']
        })
        
        
        fig11 = px.bar(dfgraph1, x="Campanhas", y=["Adicionaram ao Carrinho", "Compraram"], barmode="group",
                    color_discrete_map={"Adicionaram ao Carrinho": "#F68934", "Compraram": "#FCB33F"})

        
        fig11.update_layout(title=title_text)
        fig11.for_each_trace(lambda t: t.update(name=t.name.split('=')[0]))
        


        
        df_funnel = pd.DataFrame({
            "stage": ["Visualizações", "Entraram na Página", "Adicionaram ao Carrinho", "Compraram"],
            "value": [filtered_df['view_content'].sum(), filtered_df['landing_page_view'].sum(),
                    filtered_df['add_to_cart'].sum(), filtered_df['purchase'].sum()]
        })

        
        fig22 = px.funnel(df_funnel, x='value', y='stage', color_discrete_sequence=["#F68934"],
                        title="Funil de Conversão")

        
        fig22.update_layout(xaxis_title="Quantidade", yaxis_title="Estágios do Funil")



        filtered_df['valor_investido'] = pd.to_numeric(filtered_df['spend'], errors='coerce')
        filtered_df['impressions'] = pd.to_numeric(filtered_df['impressions'], errors='coerce')
        filtered_df['purchase'] = pd.to_numeric(filtered_df['purchase'], errors='coerce')
        filtered_df['purchase_value'] = pd.to_numeric(filtered_df['purchase_value'], errors='coerce')
        filtered_df['add_to_cart'] = pd.to_numeric(filtered_df['add_to_cart'], errors='coerce')

        
        df_card = pd.DataFrame({
            "Impressões": [filtered_df['impressions'].sum()],
            "Valor Investido": [filtered_df['valor_investido'].sum()],
            "Compras": [filtered_df['purchase'].sum()],
            "Receita": [filtered_df['purchase_value'].sum()],
            "Add to Cart": [filtered_df['add_to_cart'].sum()],
            "Tx adição ao carrinho": [filtered_df['add_to_cart'].sum() / filtered_df['landing_page_view'].sum()],
            "Tx de conversão": [filtered_df['purchase'].sum() / filtered_df['landing_page_view'].sum()]
        })

        percentage_value = round(float(df_card['Tx adição ao carrinho'].iloc[0]) * 100, 2)  
        df_card['Tx adição ao carrinho'] = percentage_value
        percentage_value = round(float(df_card['Tx de conversão'].iloc[0]) * 100, 2)
        df_card['Tx de conversão'] = percentage_value

        card2 = go.Figure()
        card2.add_trace(go.Indicator(
            mode="number+delta",
            value=df_card['Impressões'].iloc[0],
            title={"text": "Impressões"},
            delta={'reference': 400, 'relative': True},
            domain={'x': [0.1, 0.3], 'y': [0, 0.5]}))
        card2.add_trace(go.Indicator(
            mode="number+delta",
            value=df_card['Valor Investido'].iloc[0],
            number={'prefix': "R$"},
            title={"text": "Valor Investido"},
            delta={'reference': 400, 'relative': True, 'position': "top"},
            domain={'x': [0.1, 0.3], 'y': [0.5, 1]}))
        card2.add_trace(go.Indicator(
            mode = "number+delta",
            value = df_card['Compras'].iloc[0],
            title = {"text": "Compras"},
            delta = {'reference': 400, 'relative': True},
            domain = {'x': [0.7,0.9], 'y': [0.5, 1]}))
        card2.add_trace(go.Indicator(
            mode = "number+delta",
            value = df_card['Receita'].iloc[0],
            number = {'prefix': "R$"},
            title = {"text": "Receita"},
            delta = {'reference': 400, 'relative': True},
            domain = {'x': [0.4, 0.6], 'y': [0.5, 1]}
        ))
        card2.add_trace(go.Indicator(
            mode = "number+delta",
            value = df_card['Tx adição ao carrinho'].iloc[0],
            number = {'suffix': "%"},
            title = {"text": "Tx adição ao carrinho"},
            delta = {'reference': 400, 'relative': True},
            domain = {'x': [0.7, 0.9], 'y': [0, 0.5]}
        ))
        card2.add_trace(go.Indicator(
            mode = "number+delta",
            value = df_card['Tx de conversão'].iloc[0],
            number = {'suffix': "%"},
            title = {"text": "Tx de conversão"},
            delta = {'reference': 400, 'relative': True},
            domain = {'x': [0.4, 0.6], 'y': [0, 0.5]}
        ))
                    
        adset_purchase_list = []

        for adset in filtered_df['adset_name'].unique():
            purchase_sum = filtered_df[filtered_df['adset_name'] == adset]['purchase'].sum()
            adset_purchase_list.append(purchase_sum)

        
        df_table2 = pd.DataFrame({
            "Nome do Item": filtered_df['adset_name'].unique(),
            "Itens Comprados": adset_purchase_list
        })

        padding = """
        padding-top: 400px
        """

        
        c1, c2, c3 = st.columns([0.5, 0.8, 1])
        with st.container():
            c1.markdown('<h3 style="font-size: 40px; padding-top: 60px;">Resultados Detalhados</h3>', unsafe_allow_html=True)

            c2.plotly_chart(card2, use_container_width=True, width=800)  
            c2.markdown(f'<style>{padding}</style>', unsafe_allow_html=True)
            c3.table(df_table2)
        col1,col6,col2, col3 = st.columns([1,0.8,1,0.25])
        with st.container():
            col1.plotly_chart(fig11)
           
            col2.plotly_chart(fig22)
              
            col3.image("Logomarcas-SPOT-Branca.png",width = 150, use_column_width=False, ) 

        
    else:
        st.warning("As colunas 'add_to_cart' e 'purchase' não estão presentes no DataFrame.")

if __name__ == "__main__":  
    main()
    