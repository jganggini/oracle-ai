import streamlit as st
import pandas as pd

import components as component
import services.database as database
import utils as utils

# Initialize services
db_user_service = database.UserService()
utl_function_service = utils.FunctionService()

login = component.get_login()
component.get_footer()

# State mappings
map_group_state = {1: "Active", 0: "Inactive"}
reverse_map_group_state = {v: k for k, v in map_group_state.items()}

# Session state init
if "show_form" not in st.session_state:
    st.session_state["show_form"] = False
    st.session_state["form_mode"] = "create"
    st.session_state["selected_group"] = None

if login:
    st.header(":material/group: User Groups")
    st.caption("Manage user groups.")

    df_user_group = db_user_service.get_all_user_group_cache(force_update=True)

    # Display group list if form is hidden
    if not st.session_state["show_form"]:
        with st.container(border=True):
            st.badge("List User Groups")

            if df_user_group.empty:
                st.info("No user groups found.")
            else:
                df_view = df_user_group.copy()
                df_view["Status"] = df_view["USER_GROUP_STATE"].map(map_group_state)
                df_view["Edit"] = False

                df_display = df_view[[
                    "USER_GROUP_ID", "USER_GROUP_NAME", "USER_GROUP_DESCRIPTION", "USER_COUNT", "Status", "Edit"
                ]]

                edited_df = st.data_editor(
                    df_display,
                    key="data-user-group",
                    column_config={
                        "USER_GROUP_ID": st.column_config.Column("ID", disabled=True),
                        "USER_GROUP_NAME": st.column_config.Column("Name", disabled=True),
                        "USER_GROUP_DESCRIPTION": st.column_config.Column("Description", disabled=True),
                        "USER_COUNT": st.column_config.Column("Users", disabled=True),
                        "Status": st.column_config.Column("Status", disabled=True),
                        "Edit": st.column_config.CheckboxColumn("Edit", help="Mark row to edit")
                    },
                    disabled=["USER_GROUP_ID", "USER_GROUP_NAME", "USER_GROUP_DESCRIPTION", "USER_COUNT", "Status"],
                    hide_index=True,
                    use_container_width=True,
                )

                if st.button("Edit", type="primary"):
                    rows_to_edit = edited_df[edited_df["Edit"] == True]
                    if rows_to_edit.empty:
                        st.warning("Please select at least one group to edit.", icon=":material/add_alert:")
                    else:
                        for _, selected_row in rows_to_edit.iterrows():
                            group_id = selected_row["USER_GROUP_ID"]
                            group_data = df_user_group[df_user_group["USER_GROUP_ID"] == group_id].iloc[0].to_dict()
                            st.session_state.update({
                                "show_form": True,
                                "form_mode": "edit",
                                "selected_group": group_data
                            })
                            st.rerun()

    # Group form (create/edit)
    if st.session_state["show_form"]:
        mode = st.session_state["form_mode"]

        with st.container(border=True):
            st.badge("Create Group" if mode == "create" else "Edit Group", color="green" if mode == "create" else "blue")
            group_data = {
                "USER_GROUP_NAME": "",
                "USER_GROUP_DESCRIPTION": ""
            } if mode == "create" else st.session_state["selected_group"]

            col1, col2 = st.columns(2)
            with col1:
                group_name = st.text_input("Group Name", value=group_data["USER_GROUP_NAME"], disabled=(mode == "edit"))
            with col2:
                group_desc = st.text_input("Description", value=group_data["USER_GROUP_DESCRIPTION"])

            warning_msg = None
            if not group_name or not group_desc:
                warning_msg = "Please fill in all required fields."
            elif mode == "create" and group_name.strip().upper() in df_user_group["USER_GROUP_NAME"].str.upper().values:
                warning_msg = f"Group name '{group_name}' already exists."

            if warning_msg:
                st.warning(warning_msg, icon=":material/add_alert:")

            btn_col1, btn_col2, btn_col3 = st.columns([2, 2.2, 6])

            if btn_col1.button("Save", type="primary", use_container_width=True):
                if warning_msg:
                    st.stop()

                try:
                    component.get_processing(True)
                    if mode == "create":
                        msg = db_user_service.insert_user_group(
                            group_name.strip(), group_desc.strip()
                        )
                        component.get_success(msg, ":material/add_row_below:")
                    else:
                        state = reverse_map_group_state.get(group_data.get("Status", "Active"), 1)
                        msg = db_user_service.update_user_group(
                            group_data["USER_GROUP_ID"], group_name.strip(), group_desc.strip(), state
                        )
                        component.get_success(msg, ":material/update:")

                    db_user_service.get_all_user_group_cache(force_update=True)
                    st.session_state["show_form"] = False
                    st.rerun()

                except Exception as e:
                    component.get_error(f"[Error] {'Creating' if mode == 'create' else 'Updating'} Group:\n{e}")
                finally:
                    component.get_processing(False)

            if btn_col2.button("Cancel", use_container_width=True):
                st.session_state["show_form"] = False
                st.rerun()

    # Create button outside form
    if not st.session_state["show_form"]:
        if st.button("Create"):
            st.session_state["show_form"] = True
            st.session_state["form_mode"] = "create"
            st.session_state["selected_group"] = None
            st.rerun()
