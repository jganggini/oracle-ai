    BEGIN  
        DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
            host => '*',
            ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                                principal_name => 'u_s_e_r_n_a_m_e',
                                principal_type => xs_acl.ptype_db)
        );
    END;
    /
    --