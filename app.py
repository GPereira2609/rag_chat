import streamlit as st
import nest_asyncio

from rag_agent import start_rag_agent

nest_asyncio.apply()

def interface():
    st.set_page_config(
        page_title="BURRO",
        page_icon=":robot_face:",
        layout="wide",
    )

    if "qa_chain" not in st.session_state:
        with st.spinner("Conectando ao banco de dados e processando documentos..."):
            st.session_state.qa_chain = start_rag_agent()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.title("Bem-vindo ao BURRO - Bot Universitário de Respostas Rápidas e Otimizadas")
    
    st.markdown(
    """
    ⚠️ **Aviso:** As respostas apresentadas foram elaboradas com apoio de IA e baseadas nos materiais fornecidos. 
    Revise sempre com seu professor ou em fontes de estudo confiáveis.
    """,
    unsafe_allow_html=True
)

    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]): 
            st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua pergunta aqui..."):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("O BURRO está pensando..."):
                response = st.session_state.qa_chain.invoke(prompt)
                
                answer = response.get("result", "Desculpe, não consegui encontrar uma resposta para sua pergunta.")
                
                st.markdown(answer)
        
        st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    interface()