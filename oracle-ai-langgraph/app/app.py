import streamlit as st

import components as component

component.get_menu()
component.get_footer()

# Título o encabezado
st.subheader(":material/upload_file: FinAI Model")

# Mostrar la imagen
st.image("images/model.png", caption="[Diagrama ER generado con Mermaid](https://mermaid.live/view#pako:eNqtVv-q2jAUfpUQuLCBirXXqmUbiHWb7PqDq38NoWRtWsNsUtL0Mqc-0P7eI9wXW6qt2ppqxxYQbM45-b5zTvIlW-gwF0MTYm4R5HMULOmSAjkeHsD7iqMkAAwni5HVt4ZzUMn_HoBHKCI2sh0UhIj4FGyP88kgVICRZQ8y0-zL2RYJTqgPJijAV5MWjhxOQkEYPdtcJDCYC8SFbcm_BcOQuoXpdC0ZIeLoOL3Pyngk_c2OsB9gSfKa8zy1VKU84ERgTpASyDlV5waiskolbArruzbzPMwVi04P84oklCVObYcge7EJFWky6pIkSF1RfE60jFGWpoJawUOdzHU7mMBqNp7txJFggZpHZlIU5yPhkbCVfX5CZZZhgMj6ana2YvTat--6HEdq1r7trBCleK0inVpu7srCeitbBmOOnKRtijVHF1ZVN9I6VW9TSjJ_QAUJMEgOqL0giuI94yiUmwpX6u4_iyB4Hj71B6Pp5H-I4ClEa8g01sghr7-pCU56WP8ALhpQIpq7Xb2-2yo7ZoIl_ISp_E4qAS8AW6WA-VNYBfPq5Cawn1EeUM8BHv1uomXCdB9qFIFQSrtcNIf4eIEIJub4Is13EjlT0zcICI5eXn9FwMVAL6rt2yoVUIh0QmyM6CahpLo2_ib-lFI737VMhsq3yYWM3dkmM8w9xoN804w8Xqog5XBn_bmDNnWcmEfgRV56Eg_WoGQoNdCV75aDyiyhWGF51mHi7CL-PXHbSz8UCzbfUAeagse4BjmL_RU0PbSO5FccJnqRvnsylxDRr4wFJyf5Dc0t_AHNutYzGob22GzLX7fV03qdGtxAU2tqDaPZaRlas93Rui1d39fgz8MaWkPXtaYc3Z7x2Na7bRmB5bXG-Pj47Dq8vvZ_ANpi8qA)", use_container_width=True)

# Enlace adicional para abrir el editor de Mermaid en otra pestaña
st.markdown(
    """
    **Descripción del Modelo de Datos**

    El modelo de datos se compone de varias tablas que contienen información sobre diferentes aspectos de una estrategia de campañas, segmentación de clientes, interacciones y ofertas. A continuación, se presenta una descripción general de cada tabla:

    1. **interaction**: Contiene información sobre interacciones con clientes, posiblemente incluyendo datos como tipo de interacción, fecha, canal utilizado y resultado de la interacción.

    2. **campaign**: Describe las campañas de marketing, incluyendo detalles como nombre de la campaña, objetivos, fecha de inicio y finalización.

    3. **segment**: Define los segmentos de clientes, probablemente con criterios como demografía, comportamiento de compra o interacciones previas.

    4. **campaign_segment**: Representa la relación entre las campañas y los segmentos de clientes, permitiendo la asignación de campañas a segmentos específicos.

    5. **offer**: Contiene información sobre las ofertas disponibles en las campañas, tales como descuentos, promociones o beneficios adicionales.

    6. **campaign_offer**: Establece la relación entre las campañas y las ofertas, indicando qué ofertas están asociadas a cada campaña.

    7. **customer**: Almacena información sobre los clientes, como identificadores únicos, información de contacto y características relevantes para la segmentación.

    8. **channel**: Define los canales de comunicación utilizados en las interacciones y campañas, tales como correo electrónico, llamadas telefónicas o redes sociales.

    Este modelo de datos permite un análisis detallado del impacto de las campañas sobre diferentes segmentos de clientes y la efectividad de las ofertas a través de distintos canales.

    """
    "[Abrir en Mermaid Live Editor](https://mermaid.live/edit#pako:eNqtVv-q2jAUfpUQuLCBirXXqmUbiHWb7PqDq38NoWRtWsNsUtL0Mqc-0P7eI9wXW6qt2ppqxxYQbM45-b5zTvIlW-gwF0MTYm4R5HMULOmSAjkeHsD7iqMkAAwni5HVt4ZzUMn_HoBHKCI2sh0UhIj4FGyP88kgVICRZQ8y0-zL2RYJTqgPJijAV5MWjhxOQkEYPdtcJDCYC8SFbcm_BcOQuoXpdC0ZIeLoOL3Pyngk_c2OsB9gSfKa8zy1VKU84ERgTpASyDlV5waiskolbArruzbzPMwVi04P84oklCVObYcge7EJFWky6pIkSF1RfE60jFGWpoJawUOdzHU7mMBqNp7txJFggZpHZlIU5yPhkbCVfX5CZZZhgMj6ana2YvTat--6HEdq1r7trBCleK0inVpu7srCeitbBmOOnKRtijVHF1ZVN9I6VW9TSjJ_QAUJMEgOqL0giuI94yiUmwpX6u4_iyB4Hj71B6Pp5H-I4ClEa8g01sghr7-pCU56WP8ALhpQIpq7Xb2-2yo7ZoIl_ISp_E4qAS8AW6WA-VNYBfPq5Cawn1EeUM8BHv1uomXCdB9qFIFQSrtcNIf4eIEIJub4Is13EjlT0zcICI5eXn9FwMVAL6rt2yoVUIh0QmyM6CahpLo2_ib-lFI737VMhsq3yYWM3dkmM8w9xoN804w8Xqog5XBn_bmDNnWcmEfgRV56Eg_WoGQoNdCV75aDyiyhWGF51mHi7CL-PXHbSz8UCzbfUAeagse4BjmL_RU0PbSO5FccJnqRvnsylxDRr4wFJyf5Dc0t_AHNutYzGob22GzLX7fV03qdGtxAU2tqDaPZaRlas93Rui1d39fgz8MaWkPXtaYc3Z7x2Na7bRmB5bXG-Pj47Dq8vvZ_ANpi8qA)"
)

# conda activate multi-agent
# streamlit run app.py --server.port 8501

# cd app && conda activate multi-agent && streamlit run app.py --server.port 8502