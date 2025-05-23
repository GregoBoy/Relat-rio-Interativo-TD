from flask import Flask, render_template
import pandas as pd
import graficos_tesouro # Certifique-se de que este é o arquivo com as funções Pygal

app = Flask(__name__)

# Carrega o DataFrame de vendas do Tesouro Direto
df = pd.read_csv("D:/EstagioProjeto/Final/projeto/VendasTesouroDireto.csv", sep=';')

# Tratamentos de dados do Tesouro Direto
numericos = ['PU', 'Quantidade', 'Valor']
for col in numericos:
    df[col] = df[col].str.replace(',', '.').astype(float)

datas = ['Vencimento do Titulo', 'Data Venda']
for col in datas:
    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y')

# Carrega o DataFrame da Taxa Selic
df_selic = pd.read_csv("D:/EstagioProjeto/Final/projeto/taxa_selic_apurada.csv", sep=';')

# Tratamento dos dados da Taxa Selic
df_selic['Data'] = pd.to_datetime(df_selic['Data'], format='%d/%m/%Y')
df_selic['Taxa (% a.a.)'] = df_selic['Taxa (% a.a.)'].str.replace(',', '.').astype(float)

# Definir o período desejado (Janeiro de 2020 - Janeiro de 2025)
data_inicial = pd.to_datetime('2020-01-01')
data_final = pd.to_datetime('2025-01-31')

# Filtrar os dados de vendas para o período especificado
df_filtrado_periodo = df[(df['Data Venda'] >= data_inicial) & (df['Data Venda'] <= data_final)].copy()
df_filtrado_periodo['Ano Venda'] = df_filtrado_periodo['Data Venda'].dt.year
df_filtrado_periodo['Mês Venda'] = df_filtrado_periodo['Data Venda'].dt.to_period('M')
df_filtrado_periodo['Mês'] = df_filtrado_periodo['Data Venda'].dt.month
df_filtrado_periodo['Nome do Mês'] = df_filtrado_periodo['Mês'].map({
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
})

# Média do Volume Anual de Vendas por Tipo
volume_anual_tipo = df_filtrado_periodo.groupby(['Tipo Titulo', 'Ano Venda'])['Valor'].sum().reset_index(name='Volume Anual')
media_volume_anual_tipo_plot = volume_anual_tipo.groupby('Tipo Titulo')['Volume Anual'].mean().reset_index()

# Participação Percentual Mensal por Tipo
total_vendas_mensais = df_filtrado_periodo.groupby('Mês Venda')['Valor'].sum().reset_index(name='Total Vendas')
vendas_por_tipo_mensal = df_filtrado_periodo.groupby(['Mês Venda', 'Tipo Titulo'])['Valor'].sum().reset_index(name='Vendas Tipo')
df_participacao = pd.merge(vendas_por_tipo_mensal, total_vendas_mensais, on='Mês Venda')
df_participacao['Participacao Percentual'] = (df_participacao['Vendas Tipo'] / df_participacao['Total Vendas']) * 100
df_participacao['Número do Mês'] = df_participacao['Mês Venda'].dt.month
df_participacao['Nome do Mês'] = df_participacao['Número do Mês'].map({
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
})
media_participacao_mensal_tipo_plot = df_participacao.groupby(['Tipo Titulo', 'Nome do Mês'])['Participacao Percentual'].mean().reset_index()

# Comparação entre Volume de Vendas Anual e Taxa Selic Média Anual
df_selic['Ano'] = df_selic['Data'].dt.year
selic_anual = df_selic[(df_selic['Data'] >= data_inicial) & (df_selic['Data'] <= data_final)].groupby('Ano')['Taxa (% a.a.)'].mean().reset_index(name='Taxa Selic Média Anual')
selic_anual = selic_anual.rename(columns={'Ano': 'Ano Venda'})

volume_vendas_anual = df_filtrado_periodo.groupby(['Ano Venda', 'Tipo Titulo'])['Valor'].sum().reset_index()
volume_vendas_anual = volume_vendas_anual.rename(columns={'Valor': 'Volume de Vendas'})

# O DataFrame 'comparativo_anual' já contém os dados necessários para o novo gráfico
comparativo_anual = pd.merge(volume_vendas_anual, selic_anual, on='Ano Venda', how='left')

@app.route('/')
def index():
    plot_volume_anual_file = graficos_tesouro.gerar_volume_anual_grafico(media_volume_anual_tipo_plot)
    plot_participacao_mensal_file = graficos_tesouro.gerar_participacao_mensal_grafico(media_participacao_mensal_tipo_plot)
    
    # Chamada para o novo gráfico de comparação
    plot_comparacao_volume_selic_file = graficos_tesouro.gerar_comparacao_volume_selic_grafico(comparativo_anual)
    
    # Definir os insights adaptados
    insight_volume_anual = "Este gráfico de barras interativo em SVG revela a média do volume anual de vendas por tipo de título do Tesouro Direto. Ao passar o mouse sobre as barras, você pode visualizar os valores exatos, destacando quais títulos atraem maior investimento no período."
    insight_participacao_mensal = "Este gráfico de linhas interativo em SVG exibe a participação percentual mensal nas vendas totais por tipo de título. Interaja com as linhas para ver os valores de cada mês e identifique tendências e sazonalidades ao longo do ano."
    insight_comparacao_volume_selic = "Este gráfico de linhas interativo em SVG compara o volume de vendas anual de títulos do Tesouro Direto com a Taxa Selic Média Anual ao longo do tempo. Observe as tendências de ambos os indicadores e como eles podem se relacionar, com eixos independentes para facilitar a visualização de suas diferentes escalas."

    return render_template('index_pygal_files.html',
                           plot_volume_anual_file=plot_volume_anual_file,
                           plot_participacao_mensal_file=plot_participacao_mensal_file,
                           plot_comparacao_volume_selic_file=plot_comparacao_volume_selic_file,
                           insight_volume_anual=insight_volume_anual,
                           insight_participacao_mensal=insight_participacao_mensal,
                           insight_comparacao_volume_selic=insight_comparacao_volume_selic)

if __name__ == '__main__':
    app.run(debug=True)
    