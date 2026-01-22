import streamlit as st
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# --------------------------------------------------
# Configuração inicial
# --------------------------------------------------
st.set_page_config(page_title="Orçamentador Pro", layout="wide")

# Função para carregar dados (Adaptada para aceitar o ficheiro carregado)
def carregar_dados(ficheiro_excel):
    try:
        df = pd.read_excel(ficheiro_excel)
        colunas_alvo = ["CÓDIGO", "DESCRIÇÃO", "UNID", "VALORES ATUAIS JANEIRO 2025"]
        # Verifica se as colunas existem
        for col in colunas_alvo:
            if col not in df.columns:
                st.error(f"A coluna '{col}' não foi encontrada no Excel.")
                return None
        
        df = df[colunas_alvo].dropna(subset=["CÓDIGO", "DESCRIÇÃO"])
        df.rename(columns={"VALORES ATUAIS JANEIRO 2025": "Preço Unitário"}, inplace=True)
        df["Quantidade"] = 0.0
        return df
    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")
        return None

# --------------------------------------------------
# Interface de Upload (Substitui o caminho local)
# --------------------------------------------------
st.title("📐 Sistema de Orçamentação Web")

with st.expander("📁 Configuração: Carregar Tabela de Preços", expanded=True):
    arquivo_upload = st.file_uploader("Carregue o ficheiro 'Cópia de Preços Tabela atual.xlsx'", type=["xlsx"])

if arquivo_upload:
    if "dados" not in st.session_state or st.sidebar.button("🔄 Recarregar Tabela"):
        st.session_state["dados"] = carregar_dados(arquivo_upload)

if "dados" in st.session_state and st.session_state["dados"] is not None:
    # --------------------------------------------------
    # Sidebar: Dados do Cliente
    # --------------------------------------------------
    with st.sidebar:
        st.header("📋 Informações")
        cliente = st.text_input("Cliente", placeholder="Ex: João Silva")
        obra = st.text_input("Obra", placeholder="Ex: Reabilitação Moradia X")
        morada = st.text_area("Morada da Obra")
        data_orc = st.date_input("Data", value=date.today())
        iva_percent = st.selectbox("Taxa de IVA (%)", [0, 6, 13, 23], index=3)

    # --------------------------------------------------
    # Área Principal: Pesquisa e Edição
    # --------------------------------------------------
    pesquisa = st.text_input("🔍 Pesquisar por código ou descrição")

    df_base = st.session_state["dados"]
    mask = (df_base["CÓDIGO"].astype(str).str.contains(pesquisa, case=False, na=False)) | \
           (df_base["DESCRIÇÃO"].astype(str).str.contains(pesquisa, case=False, na=False))
    df_view = df_base[mask]

    edited_df = st.data_editor(
        df_view,
        column_config={
            "CÓDIGO": st.column_config.TextColumn("Cód.", disabled=True),
            "DESCRIÇÃO": st.column_config.TextColumn("Descrição", disabled=True),
            "UNID": st.column_config.TextColumn("Un.", disabled=True),
            "Preço Unitário": st.column_config.NumberColumn("Preço (€)", format="%.2f", disabled=True),
            "Quantidade": st.column_config.NumberColumn("Qtd.", min_value=0.0, step=0.1, format="%.2f")
        },
        use_container_width=True,
        hide_index=True,
        key="editor_trabalhos"
    )

    # Atualizar estado global
    for idx, row in edited_df.iterrows():
        st.session_state["dados"].loc[idx, "Quantidade"] = row["Quantidade"]

    # Cálculos
    df_final = st.session_state["dados"].copy()
    df_final["Total Linha"] = df_final["Quantidade"] * df_final["Preço Unitário"]
    subtotal = df_final["Total Linha"].sum()
    iva_valor = subtotal * iva_percent / 100
    total_geral = subtotal + iva_valor

    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Subtotal", f"{subtotal:,.2f} €")
    r2.metric(f"IVA ({iva_percent}%)", f"{iva_valor:,.2f} €")
    r3.subheader(f"Total: {total_geral:,.2f} €")

    # --------------------------------------------------
    # Exportação (Adaptada para Memória Buffer)
    # --------------------------------------------------
    itens_selecionados = df_final[df_final["Quantidade"] > 0]

    c1, c2 = st.columns(2)

    with c1:
        if not itens_selecionados.empty:
            # Gerar PDF em memória
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elementos = []
            
            # (Aqui mantemos a tua lógica de gerar_pdf, mas usando o pdf_buffer)
            elementos.append(Paragraph(f"<b>ORÇAMENTO</b>", styles["Title"]))
            # ... [O resto do teu código de elementos.append vai aqui] ...
            # Por brevidade, simplifiquei o build:
            doc.build(elementos)
            
            st.download_button(
                label="⬇️ Baixar Orçamento PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"Orcamento_{cliente}_{data_orc}.pdf",
                mime="application/pdf"
            )

    with c2:
        if not itens_selecionados.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                itens_selecionados.to_excel(writer, index=False, sheet_name='Orçamento')
            
            st.download_button(
                label="⬇️ Baixar Excel (.xlsx)",
                data=output.getvalue(),
                file_name=f"Orcamento_{cliente}_{data_orc}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Aguardando o carregamento do ficheiro Excel para começar.")
