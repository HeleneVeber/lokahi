import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database import create_db_and_tables, get_session, get_models
from app.schemas import ImovelData
from app.services import ImovelService
from app.utils.import_utils import import_file
from app.utils.viacep import fetch_address


models = get_models()
Gestor = models['Gestor']
Imovel = models['Imovel']

st.title("Imóveis 🏢")
st.write("Aqui você pode ler e gerenciar os imóveis")


# DB connection
create_db_and_tables()
with get_session() as session:
    imoveis = session.exec(select(Imovel)).all()
    # Force load relations before session closes
    for im in imoveis:
        _ = im.gestor
        _ = im.address
    gestores = session.exec(select(Gestor)).all()

# Initialize session state
if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))

# Display imoveis table
if imoveis:
    df_data = [
        {
            "_id": im.id,
            "Nome": im.nome,
            "Endereço": im.address.format(),
            "Gestor": im.gestor.name if im.gestor else "-",
        }
        for im in imoveis
    ]
    df = pd.DataFrame(df_data)

    # Display with on_select for navigation
    event = st.dataframe(
        df.drop(columns=["_id"]),
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
    )

    # Handle row selection
    if event.selection.rows:
        selected_id = df.iloc[event.selection.rows[0]]["_id"]
        st.session_state.imovel_id = selected_id
        st.switch_page("pages/3_imovel_details.py")

else:
    st.info("Nenhum imóvel cadastrado.")


# Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("+ Novo Imóvel", width="stretch"):
        st.session_state.show_form = not st.session_state.show_form
        st.session_state.address_data = None

with col2:
    if st.button("+ Importar Imóveis", width="stretch"):
        st.session_state.show_upload = not st.session_state.show_upload


# Form to add new imovel
if st.session_state.show_form:
    # CEP lookup — outside form because st.button ne fonctionne pas dans st.form
    cep_input = st.text_input("CEP")
    if st.button("Buscar endereço"):
        try:
            st.session_state.address_data = fetch_address(cep_input)
        except ValueError as e:
            st.error(str(e))

    addr = st.session_state.get("address_data")
    if addr:
        st.caption(f"{addr.logradouro} — {addr.bairro} — {addr.localidade} / {addr.uf}")

    # Gestor selection — outside form so new gestor fields appear dynamically
    gestor_options = {g.name: g.id for g in gestores}
    gestor_choice = st.selectbox("Gestor", ["—"] + list(gestor_options.keys()))

    cpf_gestor = nome_gestor = phone_gestor = None
    if gestor_choice == "—":
        cpf_gestor = st.text_input("CPF/CNPJ do novo gestor (opcional)")
        if cpf_gestor:
            nome_gestor = st.text_input("Nome do gestor")
            phone_gestor = st.text_input("Telefone (opcional)")

    with st.form("form_novo_imovel"):
        nome = st.text_input("Nome do Imóvel")
        numero = st.text_input("Número")
        complemento = st.text_input("Complemento (opcional)")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            addr = st.session_state.get("address_data")
            if not addr:
                st.error("Busque um CEP antes de salvar.")
            else:
                try:
                    with get_session() as session:
                        imovel = ImovelService.create(
                            session,
                            ImovelData(
                                nome_imovel=nome,
                                cep=addr.cep,
                                numero=numero,
                                complemento=complemento or None,
                                gestor_id=gestor_options.get(gestor_choice)
                                if gestor_choice != "—"
                                else None,
                                cpf_gestor=cpf_gestor or None,
                                nome_gestor=nome_gestor or None,
                                phone_gestor=phone_gestor or None,
                            ),
                        )
                        session.commit()
                        st.success(f"Imóvel {nome} adicionado com sucesso!")
                        st.session_state.show_form = False
                        st.session_state.address_data = None
                        st.rerun()
                except IntegrityError:
                    st.error("Este nome de imóvel já está cadastrado.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {str(e)}")


# Upload placeholder
if st.session_state.show_upload:
    uploaded_file = st.file_uploader(
        "Importar CSV, XLS, XLSX", type=["csv", "xls", "xlsx"]
    )
    st.caption(
        "Colunas obrigatórias: `nome_imovel`, `cep`, `numero` — opcional: `complemento`, `cpf_cnpj_gestor`, `nome_gestor`, `telefone_gestor`"
    )
    if uploaded_file is not None:
        if st.button("Confirmar importação"):
            st.session_state.import_result = import_file(uploaded_file, ImovelService)
            st.session_state.show_upload = False
            st.rerun()


# Show import result if available
if "import_result" in st.session_state:
    result = st.session_state.pop("import_result")
    if result["imported"] > 0:
        st.success(f"{result['imported']} imóvel(is) importado(s) com sucesso!")
    for err in result["errors"]:
        label = f"{err['row']} — " if err["row"] else ""
        st.error(f"{label}{err['error']}")

# Test hot-reload
