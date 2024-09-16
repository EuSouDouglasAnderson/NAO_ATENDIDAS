import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import altair as alt
import datetime

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
dados = load_data("chamadas.csv")

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

# Continuar com a análise dos dados filtrados...


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

# Função para calcular totais e nível de serviço
def calcular_totais(dados, ordem_meses):
    chamadas_atendidas = contar_chamadas(dados, 'Atendida', 'Quantidade Atendida')
    chamadas_nao_atendidas = contar_chamadas(dados, 'Não atendida agente', 'Quantidade Não Atendida Agente')

    # Juntar as tabelas em uma única
    chamadas_totais = chamadas_atendidas.merge(chamadas_nao_atendidas, on='Mes', how='outer').fillna(0)

    # Calcular o total de chamadas
    chamadas_totais['Total'] = chamadas_totais['Quantidade Atendida'] + chamadas_totais['Quantidade Não Atendida Agente']

    # Contar chamadas com nível de serviço
    N_servico = dados[dados['Atendida_20s'] == 1].groupby(['Mes']).size().reset_index(name='Nivel de Serviço')

    # Juntar a tabela de nível de serviço
    chamadas_totais = chamadas_totais.merge(N_servico, on='Mes', how='left').fillna(0)

    # Garantir a ordem correta dos meses
    chamadas_totais['Mes'] = pd.Categorical(chamadas_totais['Mes'], categories=ordem_meses, ordered=True)
    chamadas_totais = chamadas_totais.sort_values('Mes')

# Calcular o tempo total de atendimento
    tempo_total = dados['Tempo'].sum()
    # Converter para segundos
    total_segundos = int(tempo_total.total_seconds())

# Converter para horas, minutos e segundos
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

# Formatar como hh:mm:ss
    tempo_total_formatado = f"{horas:02}:{minutos:02}:{segundos:02}"

    # Calcular totais
    total_atendimentos = round(chamadas_totais['Total'].sum(), 2)
    total_atendida = round(chamadas_totais['Quantidade Atendida'].sum(), 2)
    total_nao_atendimentos = round(chamadas_totais['Quantidade Não Atendida Agente'].sum(), 2)
    total_Chamadas_NS = round(chamadas_totais['Nivel de Serviço'].sum(), 2)

    # Calcular a porcentagem de nível de serviço
    total_NS = round(total_Chamadas_NS / total_atendimentos * 100, 2) if total_atendimentos > 0 else 0

    return chamadas_totais, total_atendimentos, total_atendida, total_nao_atendimentos, total_Chamadas_NS, total_NS, tempo_total_formatado

# Aplicar a função de cálculo
chamadas_totais, total_atendimentos, total_atendida, total_nao_atendimentos, total_Chamadas_NS, total_NS, tempo_total_formatado = calcular_totais(filtered_data, ordem_meses)

# Seção de Totais no topo
st.header(":bar_chart: DASHBOARD DE ATENDIMENTOS")

cor_grafico = '#F4F4F4'

# Distribuição das colunas - agora com 5 colunas
col1, col2, col3, col4, col5 = st.columns([0.60, 0.45, 0.45, 0.60, 0.75])

# Exibição das métricas usando st.metric
with col1:
    st.metric(label="***TOTAL DE CHAMADAS***", value=total_atendimentos)

with col2:
    st.metric(label="***ATENDIDAS***", value=total_atendida)

with col3:
    st.metric(label="***NÃO ATENDIDAS***", value=total_nao_atendimentos)

with col4:
    st.metric(label="***NÍVEL DE SERVIÇO(%)***", value=f"{total_NS}%")

# Novo campo com a coluna col5
with col5:
    # Exemplo de nova métrica
    st.metric(label="***TEMPO EM ATENDIMENTO***", value=tempo_total_formatado)


st.markdown("---")

# Criar gráfico de linha para chamadas atendidas
graf_linha_atendidas = alt.Chart(chamadas_totais).mark_line(
    point=alt.OverlayMarkDef(color='blue', size=50, filled=True, fill='white'),  # Configura os pontos da linha com cor azul
    color='blue'  # Define a cor da linha como azul
).encode(
    x=alt.X('Mes:O', title='Mês', sort=ordem_meses),  # Define o eixo X com o mês, ordenado conforme a lista ordem_meses
    y=alt.Y('Quantidade Atendida:Q', title='Chamadas Atendidas', axis=alt.Axis(grid=False), scale=alt.Scale(domain=[0, chamadas_totais['Quantidade Atendida'].max() * 1.1])),  # Define o eixo Y com a quantidade atendida, sem grade e com uma escala ajustada
    tooltip=['Mes:O', 'Quantidade Atendida:Q']  # Adiciona tooltip para exibir mês e quantidade atendida
).properties(
    width=600,  # Define a largura do gráfico
    height=300  # Define a altura do gráfico
)

# Criar gráfico de linha para chamadas não atendidas
graf_linha_nao_atendidas = alt.Chart(chamadas_totais).mark_line(
    point=alt.OverlayMarkDef(color='orange', size=50, filled=True, fill='white'),  # Configura os pontos da linha com cor laranja
    color='orange'  # Define a cor da linha como laranja
).encode(
    x=alt.X('Mes:O', title='Mês', sort=ordem_meses),  # Define o eixo X com o mês, ordenado conforme a lista ordem_meses
    y=alt.Y('Quantidade Não Atendida Agente:Q', title='Chamadas Não Atendidas', axis=alt.Axis(grid=False), scale=alt.Scale(domain=[0, chamadas_totais['Quantidade Não Atendida Agente'].max() * 1.1])),  # Define o eixo Y com a quantidade não atendida, sem grade e com uma escala ajustada
    tooltip=['Mes:O', 'Quantidade Não Atendida Agente:Q']  # Adiciona tooltip para exibir mês e quantidade não atendida
)

# Adicionar rótulos ao gráfico de chamadas não atendidas
rotulo_nao_atendidas = graf_linha_nao_atendidas.mark_text(
    dy=-10,  # Define a distância vertical do texto em relação ao ponto
    size=12,  # Define o tamanho do texto
    color='orange'  # Define a cor do texto como laranja
).encode(
    text='Quantidade Não Atendida Agente:Q'  # Adiciona o texto dos valores da quantidade não atendida
)

# Adicionar rótulos ao gráfico de chamadas atendidas
rotulo_atendidas = graf_linha_atendidas.mark_text(
    dy=-10,  # Define a distância vertical do texto em relação ao ponto
    size=12,  # Define o tamanho do texto
    color='blue'  # Define a cor do texto como azul
).encode(
    text='Quantidade Atendida:Q'  # Adiciona o texto dos valores da quantidade atendida
)

# Combinando os gráficos de chamadas atendidas e não atendidas
graf_combined = alt.layer(graf_linha_atendidas, graf_linha_nao_atendidas, rotulo_nao_atendidas, rotulo_atendidas).resolve_scale(
    y='independent'  # Permite escalas Y independentes para cada linha
).properties(
    width=600,  # Define a largura do gráfico combinado
    height=300,  # Define a altura do gráfico combinado
    title='Chamadas Atendidas e Não Atendidas por Mês'  # Define o título do gráfico
).configure_legend(
    title=None,  # Remove o título da legenda
    orient='top-left',  # Define a orientação da legenda
    labelFontSize=12  # Define o tamanho da fonte da legenda
)

# Exibir gráfico combinado
#st.altair_chart(graf_combined, use_container_width=True)


# Definir a ordem correta das horas
ordem_horas = [str(i) for i in list(range(1, 24)) + [0]]  # Adiciona 0 após 23

# Contar a quantidade de chamadas atendidas por hora
chamadas_atendidas_hora = filtered_data[filtered_data['Status'] == 'Atendida'].groupby(['Hora']).size().reset_index(name='Quantidade Atendida')

# Contar a quantidade de chamadas não atendidas pelo agente por hora
chamadas_nao_atendidas_hora = filtered_data[filtered_data['Status'] == 'Não atendida agente'].groupby(['Hora']).size().reset_index(name='Quantidade Não Atendida Agente')

# Juntar as tabelas em uma única
chamadas_hora_do_dia = chamadas_atendidas_hora.merge(chamadas_nao_atendidas_hora, on='Hora', how='outer').fillna(0)

# Garantir que as horas são tratadas como categorias com a ordem correta
chamadas_hora_do_dia['Hora'] = pd.Categorical(chamadas_hora_do_dia['Hora'].astype(str), categories=ordem_horas, ordered=True)

# Ordenar os dados pelas horas
chamadas_hora_do_dia = chamadas_hora_do_dia.sort_values('Hora')

# Criar gráfico de barras agrupadas com matplotlib
fig, ax = plt.subplots(figsize=(8, 6))



fig.patch.set_facecolor('#F4F4F4')  # Cor de fundo da figura
ax.set_facecolor('#F4F4F4')  # Cor de fundo dos eixos

bar_width = 0.35  # Largura das barras
index = range(len(chamadas_hora_do_dia))

# Barras para chamadas atendidas
bars1 = ax.bar(index, chamadas_hora_do_dia['Quantidade Atendida'], bar_width, label='Chamadas Atendidas', color='blue')

# Barras para chamadas não atendidas
bars2 = ax.bar([i + bar_width for i in index], chamadas_hora_do_dia['Quantidade Não Atendida Agente'], bar_width, label='Chamadas Não Atendidas', color='orange')

# Configurar rótulos
ax.set_xlabel('Hora do Dia')  # Define o rótulo do eixo X
ax.set_ylabel('Quantidade de Chamadas')  # Define o rótulo do eixo Y
ax.set_title('Chamadas Atendidas e Não Atendidas por Hora do Dia')  # Define o título do gráfico
ax.set_xticks([i + bar_width / 2 for i in index])  # Define a posição dos rótulos no eixo X
ax.set_xticklabels(chamadas_hora_do_dia['Hora'])  # Define os rótulos do eixo X
ax.legend()  # Adiciona a legenda

# Adicionar rótulos de texto nas barras
for bar in bars1:
    yval = bar.get_height()  # Obtém a altura da barra
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 5, int(yval), ha='center', va='bottom', fontsize=10)  # Adiciona o texto com a quantidade de chamadas

for bar in bars2:
    yval = bar.get_height()  # Obtém a altura da barra
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 5, int(yval), ha='center', va='bottom', fontsize=10)  # Adiciona o texto com a quantidade de chamadas


duracao_contagem = filtered_data['Duração_Atendimento'].value_counts().reset_index()
duracao_contagem.columns = ['Duração_Atendimento', 'Quantidade']

total_chamadas = duracao_contagem['Quantidade'].sum()
duracao_contagem['Porcentagem'] = (duracao_contagem['Quantidade'] / total_chamadas * 100).round(2)

if not filtered_data.empty:
   
    duracao_contagem = filtered_data['Duração_Atendimento'].value_counts().reset_index()
    duracao_contagem.columns = ['Duração_Atendimento', 'Quantidade']

    total_chamadas = duracao_contagem['Quantidade'].sum()
    duracao_contagem['Porcentagem'] = duracao_contagem['Quantidade'].apply(lambda x: round((x / total_chamadas) * 100, 2))

    # Criar gráfico de barras ordenado do maior para o menor
    grafico_duracao = alt.Chart(duracao_contagem).mark_bar().encode(
        x=alt.X('Duração_Atendimento:O', title='Duração do Atendimento', sort='-y'),  # Ordenar pelo eixo y
        y=alt.Y('Quantidade:Q', title='Quantidade de Chamadas', axis=alt.Axis(grid=False)),
        color=alt.Color('Duração_Atendimento:N', scale=alt.Scale(domain=['Curto (<= 15 min)', 'Médio (15-30 min)', 'Longo (> 30 min)'], range=['blue', 'orange', 'red']), legend=alt.Legend(title="Duração do Atendimento")),
        tooltip=['Duração_Atendimento:N', 'Quantidade:Q', 'Porcentagem:Q']  # Adiciona tooltip para exibir a porcentagem
    ).properties(
        title='Quantidade de Chamadas por Duração de Atendimento',
        width=400,
        height=300
    )

    rotulo_duracao = grafico_duracao.mark_text(
        dy=-10,  # Define a distância vertical do texto em relação à barra
        size=12  # Ajusta o tamanho do texto para evitar sobreposição
    ).encode(
        text=alt.Text('Porcentagem:Q', format='.2f')  # Adiciona o texto da porcentagem com formato
    )

    grafico_com_rotulo = alt.layer(grafico_duracao, rotulo_duracao).properties(
        title='Quantidade e Porcentagem de Chamadas por Duração de Atendimento'
    )

    #st.altair_chart(grafico_com_rotulo, use_container_width=True)
else:
    st.write("Nenhum dado disponível para exibir.")

plt.tight_layout()  
#st.pyplot(fig)


# GRAFICO HORA A HORA
st.pyplot(fig)


# Dias da Semana
# Definir a ordem correta dos dias da semana
ordem_dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

# Contar a quantidade de chamadas atendidas por dia da semana
chamadas_atendidas_dia = filtered_data[filtered_data['Status'] == 'Atendida'].groupby(['Dia_Semana']).size().reset_index(name='Quantidade Atendida')

# Contar a quantidade de chamadas não atendidas pelo agente por dia da semana
chamadas_nao_atendidas_dia = filtered_data[filtered_data['Status'] == 'Não atendida agente'].groupby(['Dia_Semana']).size().reset_index(name='Quantidade Não Atendida Agente')

# Juntar as tabelas em uma única
chamadas_dias_semana = chamadas_atendidas_dia.merge(chamadas_nao_atendidas_dia, on='Dia_Semana', how='outer').fillna(0)

# Garantir que os dias da semana são tratados como categorias com a ordem correta
chamadas_dias_semana['Dia_Semana'] = pd.Categorical(chamadas_dias_semana['Dia_Semana'], categories=ordem_dias_semana, ordered=True)

# Ordenar os dados pelos dias da semana
chamadas_dias_semana = chamadas_dias_semana.sort_values('Dia_Semana')

# Criar gráfico de barras agrupadas com matplotlib
fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor('#F4F4F4')  # Cor de fundo da figura
ax.set_facecolor('#F4F4F4')  # Cor de fundo dos eixos
bar_width = 0.35  # Largura das barras
index = range(len(chamadas_dias_semana))

# Barras para chamadas atendidas
bars1 = ax.bar(index, chamadas_dias_semana['Quantidade Atendida'], bar_width, label='Chamadas Atendidas', color='blue')

# Barras para chamadas não atendidas
bars2 = ax.bar([i + bar_width for i in index], chamadas_dias_semana['Quantidade Não Atendida Agente'], bar_width, label='Chamadas Não Atendidas', color='orange')

# Configurar rótulos
ax.set_xlabel('Dia da Semana')  # Define o rótulo do eixo X
ax.set_ylabel('Quantidade de Chamadas')  # Define o rótulo do eixo Y
ax.set_title('Chamadas Atendidas e Não Atendidas por Dia da Semana')  # Define o título do gráfico
ax.set_xticks([i + bar_width / 2 for i in index])  # Define a posição dos rótulos no eixo X
ax.set_xticklabels(chamadas_dias_semana['Dia_Semana'])  # Define os rótulos do eixo X
ax.legend()  # Adiciona a legenda

# Adicionar rótulos de texto nas barras
for bar in bars1:
    yval = bar.get_height()  # Obtém a altura da barra
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 10, int(yval), ha='center', va='bottom')  # Adiciona o texto com a quantidade de chamadas

for bar in bars2:
    yval = bar.get_height()  # Obtém a altura da barra
    ax.text(bar.get_x() + bar.get_width() / 2, yval + 10, int(yval), ha='center', va='bottom')  # Adiciona o texto com a quantidade de chamadas

# Ajustar layout e exibir gráfico
plt.tight_layout()  # Ajusta o layout do gráfico
st.pyplot(fig)  # Exibe o gráfico com Streamlit


# GRAFICO MES A MES
st.altair_chart(graf_combined, use_container_width=True)

#Duração 
st.altair_chart(grafico_com_rotulo, use_container_width=True)

