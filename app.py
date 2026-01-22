import streamlit as st
import streamlit as st
import pandas as pd
import os
import io
import json
from datetime import date

# Importações para PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# 1. CONFIGURAÇÃO DA PÁGINA (Layout Estilo App)
st.set_page_config(page_title="Gestão de Lead - Orçamentador", layout="wide")

# CSS para simular interface de sistema (Cores e Bordas)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004a99; color: white; }
    .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def carregar_base():
    caminho = "Cópia de Preços Tabela atual.xlsx"
    if os.path.exists(caminho):
        try:
            df = pd.read_excel(caminho)
            df.columns = [str(c).strip() for c in df.columns]
            col_preco = "VALORES ATUAIS JANEIRO 2025"
            df = df[["CÓDIGO", "DESCRIÇÃO", "UNID", col_preco]].dropna(subset=["CÓDIGO"])
            df.rename(columns={col_preco: "Preço Unitário"}, inplace=True)
            return df
        except: pass
    return pd.DataFrame(columns=["CÓDIGO", "DESCRIÇÃO", "UNID", "Preço Unitário"])

if "itens_orcamento" not in st.session_state:
    st.session_state.itens_orcamento = pd.DataFrame(columns=["CÓDIGO", "Artigo", "UNID", "Preço Unitário", "Quantidade"])

# --- BARRA LATERAL (MENU DE NAVEGAÇÃO / BACKUP) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.title("Menu de Ações")
    
    st.info(f"📅 Data: {date.today().strftime('%d/%m/%Y')}")
    
    st.subheader("📁 Backup do Serviço")
    u_backup = st.file_uploader("Carregar JSON", type="json")
    if u_backup:
        carregados = json.load(u_backup)
        st.session_state.itens_orcamento = pd.DataFrame(carregados["itens"])
        st.success("Dados carregados!")

# --- CORPO PRINCIPAL (ESTRUTURA TIPO LEADS/APURAMENTOS) ---

# Título de Lead (Exemplo de ID dinâmico)
st.title("📑 Detalhes do Serviço / Apuramentos")
st.caption("Lead ID: 53688 | Serviço: 79385")

# LINHA 1: DADOS DA LEAD (COLUNAS)
with st.expander("👤 Informação do Cliente / Sinistro", expanded=True):
    c1, c2, c3 = st.columns(3)
    nome_cli = c1.text_input("Nome do Segurado", key="nome")
    tel_cli = c2.text_input("Contacto Telefónico", key="tel")
    email_cli = c3.text_input("Email", key="email")
    
    morada_cli = st.text_input("Local da Intervenção", key="morada")
    n_orc = st.text_input("Nº Processo Interno", value="PRO-2025-001")

# LINHA 2: ADIÇÃO DE ARTIGOS (APURAMENTOS)
st.divider()
st.subheader("🛠️ Apuramento de Custos")
tab_pesquisa, tab_manual = st.tabs(["🔎 Catálogo de Preços", "➕ Item Extraordinário"])

with tab_pesquisa:
    termo = st.text_input("Pesquisar na Tabela Ageas/CIMP:", placeholder="Ex: Vidro, Canalizador, Mão de Obra...")
    if termo:
        base = carregar_base()
        res = base[(base["DESCRIÇÃO"].str.contains(termo, case=False)) | (base["CÓDIGO"].str.contains(termo, case=False))].head(8)
        for i, row in res.iterrows():
            col1, col2, col3, col4, col5 = st.columns([1, 4, 1, 1, 0.5])
            col1.write(f"**{row['CÓDIGO']}**")
            col2.write(row["DESCRIÇÃO"])
            col3.write(f"{row['Preço Unitário']:.2f}€")
            q_val = col4.text_input("Qtd", key=f"q_{row['CÓDIGO']}", label_visibility="collapsed")
            if col5.button("➕", key=f"b_{row['CÓDIGO']}"):
                if q_val:
                    try:
                        v = float(q_val.replace(',', '.'))
                        novo = pd.DataFrame([{"CÓDIGO": row["CÓDIGO"], "Artigo": row["DESCRIÇÃO"], "UNID": row["UNID"], "Preço Unitário": row["Preço Unitário"], "Quantidade": v}])
                        st.session_state.itens_orcamento = pd.concat([st.session_state.itens_orcamento, novo], ignore_index=True)
                        st.rerun()
                    except: st.error("Qtd inválida")

with tab_manual:
    m1, m2, m3, m4 = st.columns([3, 1, 1, 1])
    m_desc = m1.text_input("Descrição da Reparação")
    m_prec = m2.number_input("Preço Acordado €", min_value=0.0)
    m_qtd = m3.number_input("Qtd.", min_value=0.0)
    if m4.button("Adicionar Linha"):
        if m_desc and m_qtd > 0:
            nm = pd.DataFrame([{"CÓDIGO": "MANUAL", "Artigo": m_desc, "UNID": "un", "Preço Unitário": m_prec, "Quantidade": m_qtd}])
            st.session_state.itens_orcamento = pd.concat([st.session_state.itens_orcamento, nm], ignore_index=True)
            st.rerun()

# LINHA 3: TABELA DE RESUMO E TOTAIS
st.divider()
if not st.session_state.itens_orcamento.empty:
    st.subheader("📋 Resumo do Orçamento")
    df_final = st.session_state.itens_orcamento.copy()
    df_final["Subtotal"] = df_final["Quantidade"] * df_final["Preço Unitário"]
    
    st.data_editor(df_final, use_container_width=True, hide_index=True)
    
    total_val = df_final["Subtotal"].sum()
    
    col_t1, col_t2 = st.columns([3, 1])
    obs_cli = col_t1.text_area("Observações Técnicas / Notas de Reparação")
    col_t2.metric("Total Orçado", f"{total_val:,.2f} €")

    # BOTÕES DE AÇÃO (EXPORTAÇÃO)
    st.divider()
    b1, b2, b3, b4 = st.columns(4)
    
    # Função PDF (Limpa sem código do artigo)
    def criar_pdf_lead(df, total):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        sty = getSampleStyleSheet()
        elems = []
        if os.path.exists("logo.png"):
            img = RLImage("logo.png", width=1.5*inch, height=0.6*inch)
            img.hAlign = 'LEFT'
            elems.append(img)
        elems.append(Paragraph(f"<b>ORÇAMENTO DE REPARAÇÃO - {n_orc}</b>", sty['Title']))
        elems.append(Paragraph(f"<b>Cliente:</b> {nome_cli}<br/><b>Local:</b> {morada_cli}<br/><b>Tel:</b> {tel_cli}", sty['Normal']))
        elems.append(Spacer(1, 15))
        data = [["Artigo / Descrição", "Qtd", "Un", "Preço", "Total"]]
        for _, r in df.iterrows():
            data.append([r['Artigo'][:60], r['Quantidade'], r['UNID'], f"{r['Preço Unitário']:.2f}€", f"{r['Subtotal']:.2f}€"])
        data.append(["", "", "", "TOTAL:", f"{total:,.2f}€"])
        t = Table(data, colWidths=[280, 40, 40, 70, 70])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
        elems.append(t)
        doc.build(elems)
        return buf.getvalue()

    with b1:
        st.download_button("📂 Gerar PDF para Cliente", data=criar_pdf_lead(df_final, total_val), file_name=f"Orcamento_{n_orc}.pdf")
    
    with b2:
        buf_x = io.BytesIO()
        with pd.ExcelWriter(buf_x, engine='xlsxwriter') as wr:
            df_final.to_excel(wr, index=False)
        st.download_button("📊 Exportar Excel (CIMP)", data=buf_x.getvalue(), file_name=f"Lead_{n_orc}.xlsx")

    with b3:
        # Guardar Rascunho
        dados_backup = {"cliente": {"nome": nome_cli, "obs": obs_cli}, "itens": st.session_state.itens_orcamento.to_dict(orient="records")}
        st.download_button("💾 Guardar Backup JSON", data=json.dumps(dados_backup), file_name=f"backup_{n_orc}.json")
    
    with b4:
        if st.button("🗑️ Limpar Lead"):
            st.session_state.itens_orcamento = pd.DataFrame(columns=["CÓDIGO", "Artigo", "UNID", "Preço Unitário", "Quantidade"])
            st.rerun()
            
