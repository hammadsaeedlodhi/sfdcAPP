import streamlit as st
import pandas as pd
import time

# ------------------- LEAD APP -------------------
def run():
    st.markdown(
        "<h2 style='text-align:center;'>👤 Salesforce Lead Manager</h2>",
        unsafe_allow_html=True
    )
    st.write("Use this app to search, add, edit, or delete Lead records in Salesforce.")

    sf = st.session_state.sf_connection

    # ------------------- CRUD OPERATIONS -------------------
    def search_leads(name_search):
        try:
            query = f"""
                SELECT Id, FirstName, LastName, Company, Title, Phone, MobilePhone, Email, Rating, LeadSource, Status,
                       Industry, AnnualRevenue, NumberOfEmployees, Street, City, State, PostalCode, Country, Description
                FROM Lead
                WHERE LastName LIKE '%{name_search}%' OR Company LIKE '%{name_search}%'
                LIMIT 100
            """
            return sf.query(query)['records']
        except Exception as e:
            st.error(f"❌ Salesforce Query Error: {e}")
            return []

    def upsert_lead(id=None, **kwargs):
        try:
            lead_data = {
                "FirstName": kwargs.get("first_name", ""),
                "LastName": kwargs.get("last_name", ""),
                "Company": kwargs.get("company", ""),
                "Title": kwargs.get("title", ""),
                "Phone": kwargs.get("phone", ""),
                "MobilePhone": kwargs.get("mobile", ""),
                "Email": kwargs.get("email", ""),
                "Rating": kwargs.get("rating", ""),
                "LeadSource": kwargs.get("lead_source", ""),
                "Status": kwargs.get("status", ""),
                "Industry": kwargs.get("industry", ""),
                "AnnualRevenue": kwargs.get("annual_revenue", ""),
                "NumberOfEmployees": kwargs.get("employees", ""),
                "Street": kwargs.get("street", ""),
                "City": kwargs.get("city", ""),
                "State": kwargs.get("state", ""),
                "PostalCode": kwargs.get("postal_code", ""),
                "Country": kwargs.get("country", ""),
                "Description": kwargs.get("description", "")
            }
            if id:
                sf.Lead.update(id, lead_data)
            else:
                sf.Lead.create(lead_data)
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_lead(id):
        try:
            sf.Lead.delete(id)
            return True, None
        except Exception as e:
            return False, str(e)

    def normalize_keys(record):
        return {
            "id": record.get("Id"),
            "first_name": record.get("FirstName", ""),
            "last_name": record.get("LastName", ""),
            "company": record.get("Company", ""),
            "title": record.get("Title", ""),
            "phone": record.get("Phone", ""),
            "mobile": record.get("MobilePhone", ""),
            "email": record.get("Email", ""),
            "rating": record.get("Rating", ""),
            "lead_source": record.get("LeadSource", ""),
            "status": record.get("Status", ""),
            "industry": record.get("Industry", ""),
            "annual_revenue": record.get("AnnualRevenue", ""),
            "employees": record.get("NumberOfEmployees", ""),
            "street": record.get("Street", ""),
            "city": record.get("City", ""),
            "state": record.get("State", ""),
            "postal_code": record.get("PostalCode", ""),
            "country": record.get("Country", ""),
            "description": record.get("Description", "")
        }

    # ------------------- LEAD FORM BUILDER -------------------
    def build_lead_fields(prefix="new", lead=None):
        if lead is None:
            lead = {}

        col_outer, spacer = st.columns([2, 1])
        with col_outer:
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                first_name = st.text_input("First Name", value=lead.get("first_name", ""), key=f"fname_{prefix}")
                last_name = st.text_input("Last Name *", value=lead.get("last_name", ""), key=f"lname_{prefix}")
                company = st.text_input("Company *", value=lead.get("company", ""), key=f"company_{prefix}")
                title = st.text_input("Title", value=lead.get("title", ""), key=f"title_{prefix}")
                phone = st.text_input("Phone", value=lead.get("phone", ""), key=f"phone_{prefix}")

            with col2:
                mobile = st.text_input("Mobile", value=lead.get("mobile", ""), key=f"mobile_{prefix}")
                email = st.text_input("Email", value=lead.get("email", ""), key=f"email_{prefix}")

                rating_opts = ["", "Hot", "Warm", "Cold"]
                rating_index = rating_opts.index(lead.get("rating", "")) if lead.get("rating", "") in rating_opts else 0
                rating = st.selectbox("Rating", rating_opts, index=rating_index, key=f"rating_{prefix}")

                source_opts = ["", "Web", "Phone Inquiry", "Partner Referral", "Purchased List", "Other"]
                src_index = source_opts.index(lead.get("lead_source", "")) if lead.get("lead_source", "") in source_opts else 0
                lead_source = st.selectbox("Lead Source", source_opts, index=src_index, key=f"source_{prefix}")

                status_opts = ["", "Open - Not Contacted", "Working - Contacted", "Closed - Converted", "Closed - Not Converted"]
                stat_index = status_opts.index(lead.get("status", "")) if lead.get("status", "") in status_opts else 0
                status = st.selectbox("Status", status_opts, index=stat_index, key=f"status_{prefix}")

            with col3:
                industry_opts = ["", "Apparel", "Banking", "Biotechnology", "Chemicals", "Communications", "Construction",
                                 "Consulting", "Education", "Electronics", "Energy", "Engineering", "Entertainment",
                                 "Environmental", "Finance", "Food & Beverage", "Government", "Healthcare", "Hospitality",
                                 "Insurance", "Machinery", "Manufacturing", "Media", "Not For Profit", "Recreation",
                                 "Retail", "Shipping", "Technology", "Telecommunications", "Transportation", "Utilities", "Other"]
                ind_index = industry_opts.index(lead.get("industry", "")) if lead.get("industry", "") in industry_opts else 0
                industry = st.selectbox("Industry", industry_opts, index=ind_index, key=f"industry_{prefix}")

                annual_revenue = st.number_input("Annual Revenue", value=float(lead.get("annual_revenue", 0) or 0), step=1000.0, key=f"revenue_{prefix}")
                employees = st.number_input("Number of Employees", value=int(lead.get("employees", 0) or 0), step=1, key=f"emp_{prefix}")

            st.text_area("Street", value=lead.get("street", ""), key=f"street_{prefix}")
            col4, col5, col6, col7 = st.columns(4)
            with col4:
                city = st.text_input("City", value=lead.get("city", ""), key=f"city_{prefix}")
            with col5:
                state = st.text_input("State", value=lead.get("state", ""), key=f"state_{prefix}")
            with col6:
                postal_code = st.text_input("Postal Code", value=lead.get("postal_code", ""), key=f"postal_{prefix}")
            with col7:
                country = st.text_input("Country", value=lead.get("country", ""), key=f"country_{prefix}")

            description = st.text_area("Description", value=lead.get("description", ""), key=f"desc_{prefix}")

        return {
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "title": title,
            "phone": phone,
            "mobile": mobile,
            "email": email,
            "rating": rating,
            "lead_source": lead_source,
            "status": status,
            "industry": industry,
            "annual_revenue": annual_revenue,
            "employees": employees,
            "street": lead.get("street", ""),
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
            "description": description
        }

    # ------------------- MAIN TABS -------------------
    tab1, tab2 = st.tabs(["🔍 Search / Edit Leads", "➕ Add New Lead"])

    # ------------------- TAB 1: SEARCH / EDIT -------------------
    with tab1:
        st.markdown("<h4>Search Leads</h4>", unsafe_allow_html=True)
        search_name = st.text_input("Enter Last Name or Company", placeholder="e.g. Johnson or ACME")

        if search_name:
            results = search_leads(search_name)
            if results:
                st.success(f"✅ Found {len(results)} record(s)")
                df = pd.DataFrame(results).drop(columns=["attributes"], errors="ignore")
                st.dataframe(df, use_container_width=True)

                options = [f"{r.get('FirstName','')} {r.get('LastName','')} | {r.get('Company','')}" for r in results]
                selected_idx = st.selectbox("Select record to edit", range(len(results)), format_func=lambda x: options[x])
                record_to_edit = normalize_keys(results[selected_idx])

                with st.form(f"edit_form_{record_to_edit['id']}"):
                    updated_data = build_lead_fields(prefix=f"edit_{record_to_edit['id']}", lead=record_to_edit)
                    updated_data["id"] = record_to_edit["id"]

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted_update = st.form_submit_button("💾 Update Record", use_container_width=True)
                        if submitted_update:
                            success, err = upsert_lead(**updated_data)
                            if success:
                                st.success("✅ Record updated successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Update failed: {err}")

                    with col2:
                        confirm_delete = st.checkbox("Confirm delete", key=f"confirm_delete_{record_to_edit['id']}")
                        delete_clicked = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                        if delete_clicked:
                            if confirm_delete:
                                success, err = delete_lead(record_to_edit["id"])
                                if success:
                                    st.warning("⚠️ Record deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Delete failed: {err}")
                            else:
                                st.warning("⚠️ Please confirm delete before proceeding.")

    # ------------------- TAB 2: ADD NEW LEAD -------------------
    with tab2:
        st.markdown("<h4>Add New Lead</h4>", unsafe_allow_html=True)
        with st.form("new_lead_form", clear_on_submit=True):
            new_lead = build_lead_fields(prefix="new")
            submitted_new = st.form_submit_button("💾 Save New Lead", use_container_width=True)

            if submitted_new:
                if new_lead["last_name"] and new_lead["company"]:
                    success, err = upsert_lead(id=None, **new_lead)
                    if success:
                        st.success("✅ Record added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add record: {err}")
                else:
                    st.warning("⚠️ Please enter Last Name and Company before saving.")
