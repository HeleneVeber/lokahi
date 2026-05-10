import streamlit as st
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database import create_db_and_tables, get_session
from app.models.address import Address
from app.models.gestor import Gestor
from app.models.imovel import Imovel
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

    addr = st.session_state.get("address_data") or {}
    if addr:
        st.caption(
            f"{addr.get('logradouro', '')} — "
            f"{addr.get('bairro', '')} — "
            f"{addr.get('localidade', '')} / {addr.get('uf', '')}"
        )

    with st.form("form_novo_imovel"):
        nome = st.text_input("Nome do Imóvel")
        gestor_options = {g.name: g.id for g in gestores}
        gestor_choice = st.selectbox("Gestor", ["—"] + list(gestor_options.keys()))
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
                    existing = session.exec(
                        select(Address).where(
                            Address.cep == addr["cep"],
                            Address.numero == numero,
                            Address.complemento == (complemento or None),
                        )
                    ).first()
                    if existing:
                        address_id = existing.id
                    else:
                        address = Address(
                            cep=addr["cep"],
                            logradouro=addr["logradouro"],
                            numero=numero,
                            complemento=complemento or None,
                            bairro=addr["bairro"],
                            cidade=addr["localidade"],
                            estado=addr["uf"],
                        )
                        session.add(address)
                        session.commit()
                        session.refresh(address)
                        address_id = address.id
                    session.close()

                    gestor_id = gestor_options.get(gestor_choice) if gestor_choice != "—" else None
                    session = get_session()
                    existing_imovel = session.exec(
                        select(Imovel).where(Imovel.address_id == address_id)
                    ).first()
                    if existing_imovel:
                        session.close()
                        st.error(f"Este endereço já está cadastrado no imóvel '{existing_imovel.nome}'.")
                    else:
                        imovel = Imovel(nome=nome, gestor_id=gestor_id, address_id=address_id)
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
    st.warning("Importação de imóveis ainda não implementada.")
