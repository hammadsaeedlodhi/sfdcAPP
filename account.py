import streamlit as st
import pandas as pd
import time

# ------------------- ACCOUNT APP -------------------
def run():
    st.markdown(
        "<h3 style='color: orange;'>🏦 Salesforce Account Management</h3>",
        unsafe_allow_html=True
    )
    st.write("You can search, add, edit, or delete Account records.")

    sf = st.session_state.sf_connection

    # --- Salesforce CRUD Operations ---
    def search_accounts(name_search):
        try:
            query = f"""
                SELECT Id, Name, Phone, Industry, Rating, BillingCountry, Active__c, Type,
                       BillingStreet, BillingCity, BillingState,
                       BillingPostalCode, ShippingStreet, ShippingCity,
                       ShippingState, ShippingPostalCode, ParentId
                FROM Account
                WHERE Name LIKE '%{name_search}%'
                LIMIT 100
            """
            results = sf.query(query)['records']
            return results
        except Exception as e:
            st.error(f"❌ Salesforce Query Error: {e}")
            return []

    def upsert_account(id=None, name="", phone="", industry="", rating="", country="", active="", account_type="",
                       billing_street="", billing_city="", billing_state="", billing_postal="",
                       shipping_street="", shipping_city="", shipping_state="", shipping_postal="", parent_id=""):
        try:
            account_data = {
                "Name": name,
                "Phone": phone,
                "Industry": industry,
                "Rating": rating,
                "BillingCountry": country,
                "Active__c": active,
                "Type": account_type,
                "BillingStreet": billing_street,
                "BillingCity": billing_city,
                "BillingState": billing_state,
                "BillingPostalCode": billing_postal,
                "ShippingStreet": shipping_street,
                "ShippingCity": shipping_city,
                "ShippingState": shipping_state,
                "ShippingPostalCode": shipping_postal,
                "ParentId": parent_id,
            }
            if id:
                sf.Account.update(id, account_data)
            else:
                sf.Account.create(account_data)
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_account(id):
        try:
            sf.Account.delete(id)
            return True, None
        except Exception as e:
            return False, str(e)

    def normalize_keys(record):
        return {
            "id": record.get("Id"),
            "name": record.get("Name", ""),
            "phone": record.get("Phone", ""),
            "industry": record.get("Industry", ""),
            "rating": record.get("Rating", ""),
            "country": record.get("BillingCountry", ""),
            "active": record.get("Active__c", ""),
            "account_type": record.get("Type", ""),
            "billing_street": record.get("BillingStreet", ""),
            "billing_city": record.get("BillingCity", ""),
            "billing_state": record.get("BillingState", ""),
            "billing_postal": record.get("BillingPostalCode", ""),
            "shipping_street": record.get("ShippingStreet", ""),
            "shipping_city": record.get("ShippingCity", ""),
            "shipping_state": record.get("ShippingState", ""),
            "shipping_postal": record.get("ShippingPostalCode", ""),
            "parent_id": record.get("ParentId", "")
        }

    # ------------------- ACCOUNT FORM BUILDER -------------------
    def build_account_fields_left_aligned(prefix="new", account=None):
        if account is None:
            account = {}

        col_outer, _ = st.columns([2, 1])
        with col_outer:
            col1, col2, col3, col4 = st.columns([12, 12, 12, 12])

            # ---------------- COLUMN 1 ----------------
            with col1:
                name = st.text_input("Name", value=account.get("name", ""), key=f"name_{prefix}")
                phone = st.text_input("Phone", value=account.get("phone", ""), key=f"phone_{prefix}")
                parent_id = st.text_input("Parent Account Id", value=account.get("parent_id", ""), key=f"parent_id_{prefix}")
                account_type_options = [""] + ["--select--",
                    "Business Partners", "Technology Partners", "Direct Customers", "Support Team", "Prospect",
                    "Customer - Direct", "Customer - Channel", "Channel Partner / Reseller",
                    "Installation Partner", "Technology Partner"
                ]
                account_type_index = account_type_options.index(account.get("account_type", "")) if account.get("account_type") in account_type_options else 0
                account_type = st.selectbox("Account Type", account_type_options, index=account_type_index, key=f"account_type_{prefix}")

            # ---------------- COLUMN 2 ----------------
            with col2:
                rating_options = [""] + ["--select--","Hot", "Warm", "Cold"]
                rating_index = rating_options.index(account.get("rating", "")) if account.get("rating", "") in rating_options else 0
                rating = st.selectbox("Rating", rating_options, index=rating_index, key=f"rating_{prefix}")
                industry_options = [""] + ["--select--",
                    "Apparel", "Banking", "Biotechnology", "Chemicals", "Communications", "Construction",
                    "Consulting", "Education", "Electronics", "Energy", "Engineering", "Entertainment",
                    "Environmental", "Finance", "Food & Beverage", "Government", "Healthcare", "Hospitality",
                    "Insurance", "Machinery", "Manufacturing", "Media", "Not For Profit", "Recreation",
                    "Retail", "Shipping", "Technology", "Telecommunications", "Transportation", "Utilities", "Other"
                ]
                industry_index = industry_options.index(account.get("industry", "")) if account.get("industry", "") in industry_options else 0
                industry = st.selectbox("Industry", industry_options, index=industry_index, key=f"industry_{prefix}")
                country = st.text_input("Country", value=account.get("country", ""), key=f"country_{prefix}")
                active_options = [""] + ["Yes", "No"]
                active_index = active_options.index(account.get("active", "")) if account.get("active", "") in active_options else 0
                active = st.selectbox("Active", active_options, index=active_index, key=f"active_{prefix}")

            # ---------------- COLUMN 3 ----------------
            with col3:
                billing_street = st.text_input("Billing Street", value=account.get("billing_street", ""), key=f"billing_street_{prefix}")
                billing_city = st.text_input("Billing City", value=account.get("billing_city", ""), key=f"billing_city_{prefix}")
                billing_state = st.text_input("Billing State", value=account.get("billing_state", ""), key=f"billing_state_{prefix}")
                billing_postal = st.text_input("Billing Postal Code", value=account.get("billing_postal", ""), key=f"billing_postal_{prefix}")

            # ---------------- COLUMN 4 ----------------
            with col4:
                shipping_street = st.text_input("Shipping Street", value=account.get("shipping_street", ""), key=f"shipping_street_{prefix}")
                shipping_city = st.text_input("Shipping City", value=account.get("shipping_city", ""), key=f"shipping_city_{prefix}")
                shipping_state = st.text_input("Shipping State", value=account.get("shipping_state", ""), key=f"shipping_state_{prefix}")
                shipping_postal = st.text_input("Shipping Postal Code", value=account.get("shipping_postal", ""), key=f"shipping_postal_{prefix}")

        return {
            "name": name,
            "phone": phone,
            "industry": industry,
            "rating": rating,
            "country": country,
            "active": active,
            "account_type": account_type,
            "billing_street": billing_street,
            "billing_city": billing_city,
            "billing_state": billing_state,
            "billing_postal": billing_postal,
            "shipping_street": shipping_street,
            "shipping_city": shipping_city,
            "shipping_state": shipping_state,
            "shipping_postal": shipping_postal,
            "parent_id": parent_id,
        }

    # ------------------- TAB LAYOUT -------------------
    tab1, tab2 = st.tabs(["🔍 Search & Edit Accounts", "➕ Create New Account"])

    # ------------------- TAB 1: SEARCH & EDIT -------------------
    with tab1:
        st.markdown("<h5 style='color: orange;'>🔍 Search Accounts by Name</h5>", unsafe_allow_html=True)

        # --- CSS to limit search input width ---
        st.markdown(
            """
            <style>
            div[data-baseweb="input"] > div {
                max-width: 480px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        search_name = st.text_input(
            "Enter Name to search for editing",
            label_visibility="collapsed",
            key="search_name_input"
        )

        if search_name:
            results = search_accounts(search_name)
            if results:
                st.success(f"✅ Found {len(results)} record(s)")

                display_results = []
                for r in results:
                    rec = r.copy()
                    rec.pop("attributes", None)
                    rec["Record Name"] = r.get("Name")
                    display_results.append(rec)

                df = pd.DataFrame(display_results)
                if "Id" in df.columns:
                    df = df.drop(columns=["Id"])
                st.dataframe(df, use_container_width=True)

                options = [f"{r['Name']} | {r.get('Phone','')} | {r.get('Industry','')}" for r in results]
                
                # Orange label for select box
            st.markdown("<div style='color: orange; font-size: 18px; font-weight: 600; margin-bottom: -12px;'>Select record to edit</div>",
            unsafe_allow_html=True)
            selected_idx = st.selectbox("", range(len(results)), format_func=lambda x: options[x])

            record_to_edit = normalize_keys(results[selected_idx])

            st.write("Edit the selected record:")
            with st.form(f"edit_form_{record_to_edit['id']}"):
                    updated_data = build_account_fields_left_aligned(prefix=f"edit_{record_to_edit['id']}", account=record_to_edit)
                    updated_data["id"] = record_to_edit["id"]

                    col1, _ = st.columns([1, 3])
                    with col1:
                        submitted_update = st.form_submit_button("💾 Update Record", key=f"update_{record_to_edit['id']}")
                        if submitted_update:
                            success, err = upsert_account(**updated_data)
                            if success:
                                st.success("✅ Record updated successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Update failed: {err}")

                        delete_clicked = st.form_submit_button("🗑️ Delete Record", key=f"delete_{record_to_edit['id']}")
                        confirm_delete = st.checkbox("Confirm delete", key=f"confirm_delete_{record_to_edit['id']}")

                        if delete_clicked:
                            if confirm_delete:
                                success, err = delete_account(record_to_edit["id"])
                                if success:
                                    st.warning("⚠️ Record deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Delete failed: {err}")
                            else:
                                st.warning("⚠️ Please check 'Confirm delete' before deleting the record.")

    # ------------------- TAB 2: CREATE NEW -------------------
    with tab2:
        st.markdown("<h3 style='color: orange;'>➕ Add New Account</h3>", unsafe_allow_html=True)
        with st.form("new_form", clear_on_submit=True):
            new_account = build_account_fields_left_aligned(prefix="new")
            submitted_new = st.form_submit_button("Save New Record")
            if submitted_new:
                if new_account["name"] and new_account["phone"]:
                    success, err = upsert_account(id=None, **new_account)
                    if success:
                        st.success("✅ Record added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add record: {err}")
                else:
                    st.warning("⚠️ Please enter at least Name and Phone before saving.")
