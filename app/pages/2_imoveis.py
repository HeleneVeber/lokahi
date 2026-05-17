import streamlit as st
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from app.database import create_db_and_tables, get_session
from app.models import Address, AddressData, Gestor, GestorData
from app.models.imovel import Imovel
from app.utils.import_utils import import_file
from app.utils.viacep import fetch_address


st.title("Imóveis 🏢")
st.write("Aqui você pode ler e gerenciar os imóveis")


# DB connection
create_db_and_tables()
session = get_session()
imoveis = session.exec(select(Imovel)).all()
gestores = session.exec(select(Gestor)).all()
addresses = session.exec(select(Address)).all()
session.close()

gestor_map = {g.id: g.name for g in gestores}
address_map = {a.id: a for a in addresses}


# Initialize session state
if "show_form" not in st.session_state:
    st.session_state.show_form = False

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False


# Display imoveis table
if imoveis:
    st.dataframe([
        {
            "Nome": im.nome,
            "Endereço": addr.format() if (addr := address_map.get(im.address_id)) else "—",
            "Gestor": gestor_map.get(im.gestor_id, "—") if im.gestor_id else "—",
            "Quartos": "—",
            "Vazios": "—",
        }
        for im in imoveis
    ])
else:
    st.info("Nenhum imóvel cadastrado.")


# Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("+ Novo Imóvel", width="stretch"):
        st.session_state.show_form = True
        st.session_state.address_data = None

with col2:
    if st.button("+ Importar Imóveis", width="stretch"):
        st.session_state.show_upload = True


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
        st.caption(
            f"{addr.logradouro} — "
            f"{addr.bairro} — "
            f"{addr.localidade} / {addr.uf}"
        )

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
                    session = get_session()
                    address = Address.get_or_create(session, AddressData(
                        cep=addr.cep,
                        logradouro=addr.logradouro,
                        numero=numero,
                        complemento=complemento or None,
                        bairro=addr.bairro,
                        localidade=addr.localidade,
                        uf=addr.uf,
                    ))

                    existing_imovel = session.exec(
                        select(Imovel).where(Imovel.address_id == address.id)
                    ).first()
                    if existing_imovel:
                        session.close()
                        st.error(f"Este endereço já está cadastrado no imóvel '{existing_imovel.nome}'.")
                    else:
                        gestor_id = None
                        if gestor_choice != "—":
                            gestor_id = gestor_options[gestor_choice]
                        elif cpf_gestor:
                            gestor = Gestor.get_or_create(session, GestorData(
                                cpf_cnpj=cpf_gestor,
                                name=nome_gestor or None,
                                phone=phone_gestor or None,
                            ))
                            session.flush()
                            gestor_id = gestor.id

                        imovel = Imovel(nome=nome, gestor_id=gestor_id, address_id=address.id)
                        session.add(imovel)
                        session.commit()
                        session.close()
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
    st.caption("Colunas obrigatórias: `nome_imovel`, `cep`, `numero` — opcional: `complemento`, `cpf_cnpj_gestor`, `nome_gestor`, `telefone_gestor`")
    if uploaded_file is not None:
        if st.button("Confirmar importação"):
            st.session_state.import_result = import_file(uploaded_file, Imovel)
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
