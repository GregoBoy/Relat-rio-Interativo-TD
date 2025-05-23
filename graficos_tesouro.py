import pygal
from pygal.style import Style
import pandas as pd
import os

# Ordem dos meses para o gráfico de participação mensal
meses_ordem = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

# Definir um estilo personalizado para os gráficos Pygal
custom_style = Style(
    background='#E8E8E8',
    plot_background='#FFFFFF',
    foreground='#534A44',
    foreground_strong='#534A44',
    foreground_subtle='#635750',
    opacity='.9',
    opacity_hover='.9',
    transition='400ms ease-in',
    font_family='google-font:Raleway',
    label_font_size=12,
    major_label_font_size=12,
    title_font_size=16,
    legend_font_size=12,
    tooltip_font_size=12,
    colors=('#E34234', '#6495ED', '#3CB371', '#F18F01', '#DA70D6', '#FFD700', '#B0C4DE', '#FFA07A', '#20B2AA', '#87CEFA')
)

# Define o diretório onde os arquivos SVG serão salvos
STATIC_FOLDER = 'static'

def gerar_volume_anual_grafico(df, filename='volume_anual.svg'):
    """
    Gera um gráfico de barras interativo para a média do volume anual de vendas por tipo de título usando Pygal.
    Salva o gráfico como um arquivo SVG no diretório estático.
    """
    # Cria o diretório 'static' se ele não existir (verificação antes de cada salvamento)
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    bar_chart = pygal.Bar(style=custom_style, title='Média do Volume Anual de Vendas por Tipo')
    
    for row in df.itertuples(index=False):
        bar_chart.add(row._0, [{'value': row._1, 'label': f'R$ {row._1:,.2f}'}])
    
    file_path = os.path.join(STATIC_FOLDER, filename)
    try:
        bar_chart.render_to_file(file_path) # Tenta salvar o gráfico
        print(f"Gráfico '{filename}' salvo com sucesso em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar o gráfico '{filename}': {e}")
        # Retorna uma string vazia ou um nome de arquivo padrão para evitar quebrar o Flask
        return "" 
    return filename

def gerar_participacao_mensal_grafico(df, filename='participacao_mensal.svg'):
    """
    Gera um gráfico de linhas interativo para a participação percentual mensal por tipo de título usando Pygal.
    Salva o gráfico como um arquivo SVG no diretório estático.
    """
    # Cria o diretório 'static' se ele não existir
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    line_chart = pygal.Line(
        style=custom_style, 
        title='Participação Percentual nas Vendas Totais mensais (Janeiro de 2020 - Janeiro de 2025)',
        x_label_rotation=20
    )
    
    line_chart.x_labels = meses_ordem
    
    df_grouped = df.groupby('Tipo Titulo')
    for tipo, data in df_grouped:
        values = []
        for mes in meses_ordem:
            mes_data = data[data['Nome do Mês'] == mes]
            if not mes_data.empty:
                values.append({'value': mes_data['Participacao Percentual'].mean(), 'label': f'{mes_data['Participacao Percentual'].mean():.2f}%'})
            else:
                values.append({'value': 0, 'label': '0.00%'})
        line_chart.add(tipo, values)

    file_path = os.path.join(STATIC_FOLDER, filename)
    try:
        line_chart.render_to_file(file_path)
        print(f"Gráfico '{filename}' salvo com sucesso em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar o gráfico '{filename}': {e}")
        return ""
    return filename

def gerar_comparacao_volume_selic_grafico(df, filename='comparacao_volume_selic.svg'):
    """
    Gera um gráfico de linhas interativo comparando o Volume de Vendas Anual (por tipo de título) e a Taxa Selic Média Anual usando Pygal.
    Utiliza dois eixos Y para lidar com as diferentes escalas.
    Salva o gráfico como um arquivo SVG no diretório estático.
    """
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    # Obter os anos únicos para os rótulos do eixo X
    years = sorted(df['Ano Venda'].unique())
    
    # Calcular o range para o eixo secundário da Selic
    selic_min = df['Taxa Selic Média Anual'].min() * 0.9
    selic_max = df['Taxa Selic Média Anual'].max() * 1.1

    line_chart = pygal.Line(
        style=custom_style,
        title='Comparação do Volume de Vendas por Título e Taxa Selic Média Anual (2020 - 2025)',
        x_label_rotation=20,
        secondary_range=(selic_min, selic_max),
        y_title='Volume de Vendas (R$)',
        secondary_y_title='Taxa Selic (% a.a.)',
        x_labels=[str(year) for year in years] # Define os rótulos do eixo X como os anos
    )

    # Adicionar uma série de linha para cada 'Tipo Titulo' para o Volume de Vendas
    unique_titles = df['Tipo Titulo'].unique()
    for title in unique_titles:
        title_data = df[df['Tipo Titulo'] == title].sort_values('Ano Venda')
        volume_values = []
        for year in years:
            # Obter o volume para o tipo de título específico e ano
            # Usamos .sum() caso haja múltiplas entradas para o mesmo tipo de título em um ano
            volume = title_data[title_data['Ano Venda'] == year]['Volume de Vendas'].sum()
            volume_values.append({'value': volume, 'label': f'R$ {volume:,.2f}'})
        line_chart.add(f'Volume ({title})', volume_values)

    # Adicionar a série da Taxa Selic Média Anual no eixo secundário
    # É importante pegar os valores únicos da Selic por ano para evitar duplicações na série
    unique_selic_per_year = df[['Ano Venda', 'Taxa Selic Média Anual']].drop_duplicates().sort_values('Ano Venda')
    
    selic_values = []
    for year in years:
        # Pega a Taxa Selic Média Anual para o ano específico
        selic_rate = unique_selic_per_year[unique_selic_per_year['Ano Venda'] == year]['Taxa Selic Média Anual'].iloc[0]
        selic_values.append({'value': selic_rate, 'label': f'{selic_rate:.2f}%'})
    line_chart.add('Taxa Selic Média Anual', selic_values, secondary=True) # Define como série secundária

    file_path = os.path.join(STATIC_FOLDER, filename)
    try:
        line_chart.render_to_file(file_path)
        print(f"Gráfico '{filename}' salvo com sucesso em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar o gráfico '{filename}': {e}")
        return ""
    return filename
