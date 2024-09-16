import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import altair as alt
import datetime

pip install matplotlib


# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path, sep=",", encoding="utf-8")
    # Convertendo a coluna 'Data' para datetime
    data['Data'] = pd.to_datetime(data['Data'])
    # Convertendo a coluna 'Hora' para tipo int
    data['Hora'] = pd.to_numeric(data['Hora'], errors='coerce').astype('Int64') 
    # Supondo que a coluna 'Tempo' já foi convertida para timedelta antes deste ponto
    data['Tempo'] = pd.to_timedelta(data['Tempo'])
    return data

# Carregar os dados
dados = load_data("chamadas_nao_atendidas.csv")

# Configurações de estilo
cor_grafico = '#FFFFFF'
altura_grafico = 250

# Função para aplicar filtros
def aplicar_filtros(dados, destino, mes, dia_semana, data_inicial, data_final):
    if destino != "Todos":
        dados = dados[dados['Destino'] == destino]
    if mes != "Todos":
        dados = dados[dados['Mes'] == mes]
    if dia_semana != "Todos":
        dados = dados[dados['Dia_Semana'] == dia_semana]
    # Aplicar o filtro de data
    dados = dados[(dados['Data'].dt.date >= data_inicial) & (dados['Data'].dt.date <= data_final)]
    return dados

# Sidebar para filtros
with st.sidebar:
    st.image('Imagem_easy_2.png', width=200)
    st.subheader("MENU - DASHBOARD DE ATENDIMENTOS")
    dados['Data'] = pd.to_datetime(dados['Data'])
    data_inicial = dados['Data'].min().date()
    data_final = dados['Data'].max().date()
    periodo = st.slider('Selecione o período', min_value=data_inicial, max_value=data_final, value=(data_inicial, data_final))
    destino_opcoes = ["Todos"] + list(dados['Destino'].unique())
    fDestino = st.selectbox("Selecione o Analista:", options=destino_opcoes)
    meses_opcoes = ["Todos"] + list(dados['Mes'].unique())
    fMes = st.selectbox("Selecione o Mês:", options=meses_opcoes)
    dias_semana_opcoes = ["Todos"] + list(dados['Dia_Semana'].unique())
    fDia_Semana = st.selectbox("Selecione o Dia da Semana:", options=dias_semana_opcoes)

# Filtrar os dados com base nas seleções
filtered_data = aplicar_filtros(dados, fDestino, fMes, fDia_Semana, periodo[0], periodo[1])

# Verificação de dados filtrados
if filtered_data.empty:
    st.write("Nenhum dado encontrado com os filtros selecionados.")

# Definir a ordem correta dos meses
ordem_meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

# Função para contar chamadas atendidas e não atendidas
def contar_chamadas(dados, status, nome_coluna):
    return dados[dados['Status'] == status].groupby(['Mes']).size().reset_index(name=nome_coluna)

# Função para calcular totais
def calcular_totais(dados, ordem_meses):
    chamadas_nao_atendidas = contar_chamadas(dados, 'Não atendida', 'Quantidade Não Atendida')
    
    # Garantir a ordem correta dos meses
    chamadas_nao_atendidas['Mes'] = pd.Categorical(chamadas_nao_atendidas['Mes'], categories=ordem_meses, ordered=True)
    chamadas_nao_atendidas = chamadas_nao_atendidas.sort_values('Mes')
    
    return chamadas_nao_atendidas

# Aplicar a função de cálculo
chamadas_totais = calcular_totais(filtered_data, ordem_meses)

# Seção de Totais no topo
st.header(":bar_chart: DASHBOARD DE ATENDIMENTOS")

# Distribuição das colunas - agora com 1 coluna
col3 = st.columns([1])

# Exibição da métrica usando st.metric
with col3[0]:
    total_nao_atendimentos = chamadas_totais['Quantidade Não Atendida'].sum()
    st.metric(label="***NÃO ATENDIDAS***", value=total_nao_atendimentos)

st.markdown("---")

# Criar gráfico de linha para chamadas não atendidas
graf_linha_nao_atendidas = alt.Chart(chamadas_totais).mark_line(
    point=alt.OverlayMarkDef(color='orange', size=50, filled=True, fill='white'),  # Configura os pontos da linha com cor laranja
    color='orange'  # Define a cor da linha como laranja
).encode(
    x=alt.X('Mes:O', title='Mês', sort=ordem_meses),  # Define o eixo X com o mês, ordenado conforme a lista ordem_meses
    y=alt.Y('Quantidade Não Atendida:Q', title='Chamadas Não Atendidas', axis=alt.Axis(grid=False), scale=alt.Scale(domain=[0, chamadas_totais['Quantidade Não Atendida'].max() * 1.1])),  # Define o eixo Y com a quantidade não atendida, sem grade e com uma escala ajustada
    tooltip=['Mes:O', 'Quantidade Não Atendida:Q']  # Adiciona tooltip para exibir mês e quantidade não atendida
).properties(
    width=600,  # Define a largura do gráfico
    height=300  # Define a altura do gráfico
)

# Adicionar rótulos ao gráfico de chamadas não atendidas
rotulo_nao_atendidas = graf_linha_nao_atendidas.mark_text(
    dy=-10,  # Define a distância vertical do texto em relação ao ponto
    size=12,  # Define o tamanho do texto
    color='orange'  # Define a cor do texto como laranja
).encode(
    text='Quantidade Não Atendida:Q'  # Adiciona o texto dos valores da quantidade não atendida
)

# Combinar o gráfico de linha com os rótulos
grafico_completo_nao_atendidas = graf_linha_nao_atendidas + rotulo_nao_atendidas

# Exibir o gráfico de chamadas não atendidas
st.altair_chart(grafico_completo_nao_atendidas, use_container_width=True)

# Definir a ordem correta das horas
ordem_horas = [str(i) for i in list(range(1, 24)) + [0]]  # Adiciona 0 após 23

# Contar a quantidade de chamadas não atendidas por hora
chamadas_nao_atendidas_hora = filtered_data[filtered_data['Status'] == 'Não atendida'].groupby(['Hora']).size().reset_index(name='Quantidade Não Atendida')

# Garantir que as horas são tratadas como categorias com a ordem correta
ordem_horas = [str(h) for h in range(24)]  # Lista com horas de 0 a 23
chamadas_nao_atendidas_hora['Hora'] = pd.Categorical(chamadas_nao_atendidas_hora['Hora'].astype(str), categories=ordem_horas, ordered=True)

# Ordenar os dados pelas horas
chamadas_nao_atendidas_hora = chamadas_nao_atendidas_hora.sort_values('Hora')

# Criar gráfico de barras com matplotlib
fig, ax = plt.subplots(figsize=(8, 6))

fig.patch.set_facecolor('#F4F4F4')  # Cor de fundo da figura
ax.set_facecolor('#F4F4F4')  # Cor de fundo dos eixos

bar_width = 0.35  # Largura das barras
index = range(len(chamadas_nao_atendidas_hora))

# Barras para chamadas não atendidas
bars = ax.bar(index, chamadas_nao_atendidas_hora['Quantidade Não Atendida'], bar_width, label='Chamadas Não Atendidas', color='orange')

# Configurar rótulos
ax.set_xlabel('Hora do Dia')  # Define o rótulo do eixo X
ax.set_ylabel('Quantidade de Chamadas Não Atendidas')  # Define o rótulo do eixo Y
ax.set_title('Chamadas Não Atendidas por Hora do Dia')  # Define o título do gráfico
ax.set_xticks(index)  # Define a posição dos rótulos no eixo X
ax.set_xticklabels(chamadas_nao_atendidas_hora['Hora'])  # Define os rótulos do eixo X
ax.legend()  # Adiciona a legenda

# Adicionar rótulos de texto nas barras
for bar in bars:
    yval = bar.get_height()  # Obtém a altura da barra
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 5, int(yval), ha='center', va='bottom', fontsize=10)  # Adiciona o texto com a quantidade de chamadas

# Exibir o gráfico no Streamlit
st.pyplot(fig)




# Contar a quantidade de chamadas não atendidas por dia da semana
chamadas_nao_atendidas_dia = filtered_data[filtered_data['Status'] == 'Não atendida'].groupby(['Dia_Semana']).size().reset_index(name='Quantidade Não Atendida')

# Garantir que os dias da semana estão na ordem correta
dias_da_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
chamadas_nao_atendidas_dia['Dia_Semana'] = pd.Categorical(chamadas_nao_atendidas_dia['Dia_Semana'], categories=dias_da_semana, ordered=True)

# Ordenar os dados pelos dias da semana
chamadas_nao_atendidas_dia = chamadas_nao_atendidas_dia.sort_values('Dia_Semana')

# Criar gráfico de barras para chamadas não atendidas por dia da semana
fig2, ax2 = plt.subplots(figsize=(8, 6))
fig2.patch.set_facecolor('#F4F4F4')  # Cor de fundo da figura
ax2.set_facecolor('#F4F4F4')  # Cor de fundo dos eixos

index_dia = range(len(chamadas_nao_atendidas_dia))

# Barras para chamadas não atendidas por dia da semana
bars_dia = ax2.bar(index_dia, chamadas_nao_atendidas_dia['Quantidade Não Atendida'], bar_width, label='Chamadas Não Atendidas', color='orange')

# Configurar rótulos
ax2.set_xlabel('Dia da Semana')  # Define o rótulo do eixo X
ax2.set_ylabel('Quantidade de Chamadas Não Atendidas')  # Define o rótulo do eixo Y
ax2.set_title('Chamadas Não Atendidas por Dia da Semana')  # Define o título do gráfico
ax2.set_xticks(index_dia)  # Define a posição dos rótulos no eixo X
ax2.set_xticklabels(chamadas_nao_atendidas_dia['Dia_Semana'])  # Define os rótulos do eixo X
ax2.legend()  # Adiciona a legenda

# Adicionar rótulos de texto nas barras
for bar in bars_dia:
    yval = bar.get_height()  # Obtém a altura da barra
    ax2.text(bar.get_x() + bar.get_width() / 2, yval + 5, int(yval), ha='center', va='bottom', fontsize=10)  # Adiciona o texto com a quantidade de chamadas

# Exibir o gráfico no Streamlit
st.pyplot(fig2)
