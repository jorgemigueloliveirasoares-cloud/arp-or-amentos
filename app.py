import streamlit as st
import pandas as pd
import plotly.express as px # Para gráficos dinâmicos

# 1. CONFIGURAÇÃO DA INTERFACE
st.set_page_config(page_title="Dashboard de Processos", layout="wide")

# Estilo para os cartões de estado
st.markdown("""
    <style>
    .status-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO PARA CARREGAR O EXCEL (Base de Dados de Processos)
@st.cache_data
def carregar_dados():
    # Substitua pelo nome real do seu ficheiro que contém os processos e estados
    caminho = "Cópia de Preços Tabela atual.xlsx" 
    try:
        df = pd.read_excel(caminho)
        # Limpeza básica de nomes de colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro: {e}")
        return pd.DataFrame()

df = carregar_dados()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros de Visualização")
if not df.empty:
    # Ajuste 'ESTADO' para o nome da coluna que define o status no seu Excel
    coluna_estado = "ESTADO" if "ESTADO" in df.columns else df.columns[-1]
    
    estados = st.sidebar.multiselect(
        "Filtrar por Estado:",
        options=df[coluna_estado].unique(),
        default=df[coluna_estado].unique()
    )
    
    df_filtrado = df[df[coluna_estado].isin(estados)]
else:
    df_filtrado = df

# --- CORPO PRINCIPAL ---
st.title("📊 Monitorização de Processos")

if not df.empty:
    # 3. INDICADORES RÁPIDOS (KPIs)
    c1, c2, c3, c4 = st.columns(4)
    total_procs = len(df_filtrado)
    
    c1.metric("Total Processos", total_procs)
    # Exemplo de lógica para estados específicos
    if "ABERTO" in df_filtrado[coluna_estado].values:
        c2.metric("Abertos", len(df_filtrado[df_filtrado[coluna_estado] == "ABERTO"]))
    if "EM CURSO" in df_filtrado[coluna_estado].values:
        c3.metric("Em Curso", len(df_filtrado[df_filtrado[coluna_estado] == "EM CURSO"]))
    c4.metric("Última Atualização", date.today().strftime("%d/%m/%Y"))

    st.divider()

    # 4. VISUALIZAÇÃO GRÁFICA
    col_graph1, col_graph2 = st.columns([1, 1])
    
    with col_graph1:
        st.subheader("Distribuição por Estado")
        fig_estado = px.pie(df_filtrado, names=coluna_estado, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_graph2:
        st.subheader("Volume de Processos")
        # Exemplo se tiver uma coluna de 'TÉCNICO' ou 'DATA'
        col_agrupar = "TÉCNICO" if "TÉCNICO" in df_filtrado.columns else coluna_estado
        fig_bar = px.bar(df_filtrado[col_agrupar].value_counts(), orientation='h', labels={'value':'Qtd', 'index': col_agrupar})
        st.plotly_chart(fig_bar, use_container_width=True)

    # 5. TABELA INTERATIVA (ESTADO DOS PROCESSOS)
    st.subheader("📂 Lista Detalhada de Processos")
    
    # Pesquisa Global
    search = st.text_input("Pesquisar Processo, Segurado ou Localidade...")
    if search:
        mask = df_filtrado.apply(lambda x: x.astype(str).str.contains(search, case=False)).any(axis=1)
        df_exibir = df_filtrado[mask]
    else:
        df_exibir = df_filtrado

    st.dataframe(
        df_exibir, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            coluna_estado: st.column_config.SelectboxColumn(
                "Estado",
                options=["ABERTO", "EM CURSO", "PENDENTE", "FECHADO"],
                required=True,
            )
        }
    )

    # 6. EXPORTAÇÃO
    st.download_button(
        "📥 Descarregar Relatório Atual (Excel)",
        data=df_exibir.to_csv(index=False).encode('utf-8'),
        file_name="estado_processos.csv",
        mime="text/csv"
    )

else:
    st.warning("Por favor, certifique-se que o ficheiro Excel tem as colunas necessárias (Ex: ESTADO, NOME, PROCESSO).")
