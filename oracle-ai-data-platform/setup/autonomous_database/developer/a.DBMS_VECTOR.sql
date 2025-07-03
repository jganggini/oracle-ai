    DECLARE
      jo json_object_t;
    BEGIN
      jo := json_object_t();
      jo.put('compartment_ocid','c_o_m_p_a_r_t_m_e_n_t__id');
      jo.put('user_ocid','u_s_e_r__o_c_i_d');
      jo.put('tenancy_ocid','t_e_n_a_n_c_y__o_c_i_d');
      jo.put('private_key','p_r_i_v_a_t_e__k_e_y');
      jo.put('fingerprint','f_i_n_g_e_r_p_r_i_n_t');
      DBMS_VECTOR.CREATE_CREDENTIAL(
        credential_name => 'c_r_e_d_e_n_t_i_a_l__n_a_m_e',
        params          => json(jo.to_string));
    END;
    /
    --