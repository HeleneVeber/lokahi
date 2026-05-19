import streamlit as st
from sqlmodel import select

from app.database import create_db_and_tables, get_session
from app.models import Gestor, GestorData
from app.utils.import_utils import import_file

st.title("Gestores de Coliving 🏠")
st.write("Aqui você pode ler e gerenciar os gestores de coliving")


# DB connection
create_db_and_tables()
session = get_session()
gestores = session.exec(select(Gestor)).all()
session.close()


# Initialize session state
if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))


# Display gestores in a table
if gestores:
    st.dataframe(
        [g.display() for g in gestores],
    )
else:
    st.info("Nenhum gestor cadastrado.")


# Show buttons sude by side
col1, col2 = st.columns(2)

with col1:
    if st.button("+ Novo Gestor", width="stretch"):
        st.session_state.show_form = not st.session_state.show_form

with col2:
    if st.button("+ Importar Gestores", width="stretch"):
        st.session_state.show_upload = not st.session_state.show_upload


# Form to add new gestor
if st.session_state.show_form:
    with st.form("form_novo_gestor"):
        name = st.text_input("Nome Completo")
        cpf_cnpj = st.text_input("CPF ou CNPJ")
        phone = st.text_input("Telefone")
        submitted = st.form_submit_button("Salvar")

        if submitted:
            try:
                with get_session() as session:
                    gestor, created = Gestor.get_or_create(
                        session,
                        GestorData(name=name, cpf_cnpj=cpf_cnpj, phone=phone or None),
                    )
                    if not created:
                        st.error("Este CPF/CNPJ já está cadastrado.")
                    else:
                        session.commit()
                        st.session_state.success_message = (
                            f"Gestor {name} adicionado com sucesso!"
                        )
                        st.session_state.show_form = False
                        st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Erro ao salvar: {str(e)}")


# Placeholder for upload functionality
if st.session_state.show_upload:
    uploaded_file = st.file_uploader(
        "Importar CSV, XLS, XLSX", type=["csv", "xls", "xlsx"]
    )
    st.caption("Colunas obrigatórias: `name`, `cpf_cnpj` — opcional: `phone`")
    if uploaded_file is not None:
        if st.button("Confirmar importação"):
            st.session_state.import_result = import_file(uploaded_file, Gestor)
            st.session_state.show_upload = False
            st.rerun()


# Show import result if available
if "import_result" in st.session_state:
    result = st.session_state.pop("import_result")
    if result["imported"] > 0:
        st.success(f"{result['imported']} gestor(es) importado(s) com sucesso!")
    for err in result["errors"]:
        label = f"{err['row']} — " if err["row"] else ""
        st.error(f"{label}{err['error']}")
