BEGIN
    EXECUTE IMMEDIATE 'CREATE TABLE telco_customers (
        customer_id     NUMBER PRIMARY KEY,
        customer_code   VARCHAR2(10),
        first_name      VARCHAR2(255),
        last_name       VARCHAR2(255),
        email           VARCHAR2(255),
        phone_number    VARCHAR2(50),
        address         VARCHAR2(255),
        city            VARCHAR2(100),
        state           VARCHAR2(100),
        postal_code     VARCHAR2(50),
        country         VARCHAR2(100)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_contract_type (
        contract_id     NUMBER PRIMARY KEY,
        customer_id     NUMBER,
        contract_type   VARCHAR2(20),
        CONSTRAINT fk_customer_contract FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_customer_calls (
        call_id         NUMBER PRIMARY KEY,
        customer_id     NUMBER,
        customer_code   VARCHAR2(10),
        call_html       CLOB,
        call_text       CLOB,
        call_sentiments_sentence CLOB,
        call_sentiments_sentence_metric   VARCHAR2(250),
        call_sentiments_sentence_score    NUMBER,
        call_sentiments_aspect   CLOB,
        call_date       DATE,
        CONSTRAINT fk_customer_call FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';

    EXECUTE IMMEDIATE 'CREATE SEQUENCE call_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE';

    EXECUTE IMMEDIATE 'CREATE OR REPLACE TRIGGER trg_telco_customer_calls_id
    BEFORE INSERT ON telco_customer_calls
    FOR EACH ROW
    WHEN (NEW.call_id IS NULL)
    BEGIN
    :NEW.call_id := call_id_seq.NEXTVAL;
    END';
    
    EXECUTE IMMEDIATE 'CREATE TABLE telco_claim_resolution_options (
        resolution_option_id NUMBER PRIMARY KEY,
        resolution_type      VARCHAR2(50),
        description          VARCHAR2(255),
        discount_value       NUMBER(5, 2),
        applicable_product   VARCHAR2(100),
        resolution_notes     VARCHAR2(4000)
    )';

    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1001, ''Oferta de Retención'', ''20% de descuento en la próxima factura por retención'', 20.00, ''Plan de Internet'', ''Oferta de retención aplicada para la fidelidad del cliente'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1002, ''Oferta de Descuento'', ''15% de descuento durante 6 meses en servicios combinados'', 15.00, ''TV + Internet'', ''Descuento ofrecido en servicio combinado'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1003, ''Ajuste de Servicio'', ''Actualización gratuita al paquete premium por 3 meses'', 0.00, ''Plan Móvil'', ''Ajuste de servicio al paquete premium'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1004, ''Reemplazo de Producto'', ''Reemplazo del módem defectuoso sin costo adicional'', 0.00, ''Módem'', ''Módem defectuoso reemplazado bajo garantía'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1005, ''Oferta de Retención'', ''Suscripción gratuita a servicio de streaming por 1 año'', 0.00, ''Servicio de Streaming'', ''Oferta de retención para clientes premium'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1006, ''Oferta de Descuento'', ''10% de descuento en llamadas internacionales por 12 meses'', 10.00, ''Llamadas Internacionales'', ''Descuento ofrecido para quienes llaman frecuentemente al extranjero'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1007, ''Ajuste de Servicio'', ''Incremento del límite de datos a 200GB por mes'', 0.00, ''Plan de Internet'', ''Límite de datos aumentado para usuarios intensivos'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1008, ''Reemplazo de Producto'', ''Reemplazo del decodificador antiguo por el modelo más reciente'', 0.00, ''Decodificador'', ''Actualización del cliente al modelo más reciente de decodificador'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1009, ''Oferta de Retención'', ''5% de descuento en las próximas 5 facturas'', 5.00, ''Todos los Servicios'', ''Oferta general de retención para reducir la pérdida de clientes'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1010, ''Oferta de Descuento'', ''25% de descuento en la compra de nuevos dispositivos'', 25.00, ''Dispositivos'', ''Descuento promocional en la compra de dispositivos'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1011, ''Oferta de Retención'', ''Sesión de capacitación gratuita sobre el uso del producto'', 0.00, ''Todos los Productos'', ''Sesión de capacitación gratuita ofrecida para el conocimiento del producto'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1012, ''Oferta de Retención'', ''Actualización a una suscripción premium sin costo adicional'', 0.00, ''Todos los Servicios'', ''Actualización gratuita a suscripción premium'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1013, ''Oferta de Retención'', ''Puntos de lealtad adicionales añadidos a la cuenta'', 0.00, ''Todos los Servicios'', ''Puntos de lealtad adicionales añadidos'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1014, ''Reemplazo de Producto'', ''Garantía extendida en productos comprados'', 0.00, ''Dispositivos'', ''Garantía extendida ofrecida'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1015, ''Ajuste de Servicio'', ''Crédito de servicio por inconvenientes causados'', 20.00, ''Todos los Servicios'', ''Cuenta de servicio acreditada por inconvenientes'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1016, ''Ajuste de Servicio'', ''Soporte prioritario durante los próximos 6 meses'', 0.00, ''Todos los Servicios'', ''Soporte prioritario concedido'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1017, ''Reemplazo de Producto'', ''Intercambio de equipo antiguo por la nueva versión'', 0.00, ''Equipos'', ''Equipo intercambiado por la última versión'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1018, ''Oferta de Retención'', ''Bonificación por referir nuevos clientes'', 10.00, ''Todos los Servicios'', ''Bonificación añadida por referir nuevos clientes'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1019, ''Ajuste de Servicio'', ''Exención de cargos por pago atrasado'', 0.00, ''Facturación'', ''Cargos por pago atrasado exentos para buenos clientes'')';
    EXECUTE IMMEDIATE 'INSERT INTO telco_claim_resolution_options (resolution_option_id, resolution_type, description, discount_value, applicable_product, resolution_notes) VALUES (1020, ''Oferta de Descuento'', ''Descuento por renovación anticipada de servicios'', 10.00, ''Todos los Servicios'', ''Descuento por renovación anticipada de contrato'')';
END;