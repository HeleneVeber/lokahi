import streamlit as st

from app.database import create_db_and_tables, get_session, get_models

Imovel = get_models()['Imovel']

create_db_and_tables()

imovel_id = st.session_state.get("imovel_id")

if not imovel_id:
    st.error("ID do imóvel não fornecido")
    st.stop()

with get_session() as session:
    imovel = session.get(Imovel, int(imovel_id))
    if imovel:
        # Force loading relations before session closes
        _ = imovel.quartos
        _ = imovel.gestor
        _ = imovel.address

if not imovel:
    st.error(f"Imóvel com ID {imovel_id} não encontrado")
    st.stop()

st.title(imovel.nome)
st.write(f"Endereço: {imovel.address.format()}")
st.write(f"Gestor: {imovel.gestor.name if imovel.gestor else '-'}")
st.write(f"Total de quartos: {imovel.total_quartos}")
