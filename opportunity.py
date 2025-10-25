import streamlit as st
import pandas as pd
import time

# ------------------- OPPORTUNITY APP -------------------
def run():
    # Header (Left aligned, orange icon)
    st.markdown(
        "<h2 style='text-align:left; color:#FF8800;'>💼 Salesforce Opportunity Manager</h2>",
        unsafe_allow_html=True
    )
    st.write("Use this app to search, add, edit, or delete Opportunity records in Salesforce.")

    sf = st.session_state.sf_connection

    # ------------------- CRUD OPERATIONS -------------------
    def search_opportunities(name_search):
        try:
            query = f"""
                SELECT Id, Name, Account.Id, Account.Name, StageName, CloseDate, Amount, Probability, Type,
                       LeadSource, NextStep, Description, ForecastCategoryName
                FROM Opportunity
                WHERE Name LIKE '%{name_search}%'
                LIMIT 100
            """
            results = sf.query(query)['records']
            for r in results:
                if "Account" in r and r["Account"]:
                    r["AccountName"] = r["Account"].get("Name", "")
                    r["AccountId"] = r["Account"].get("Id", "")
                else:
                    r["AccountName"] = ""
                    r["AccountId"] = ""
                r.pop("Account", None)
            return results
        except Exception as e:
            st.error(f"❌ Salesforce Query Error: {e}")
            return []

    def upsert_opportunity(id=None, name="", account_id="", stage="", close_date="", amount="", probability="",
                           opp_type="", lead_source="", next_step="", description="", forecast_category=""):
        try:
            opp_data = {
                "Name": name,
                "StageName": stage,
                "CloseDate": close_date,
                "Amount": amount,
                "Probability": probability,
                "Type": opp_type,
                "LeadSource": lead_source,
                "NextStep": next_step,
                "Description": description,
                "ForecastCategoryName": forecast_category
            }
            if account_id:
                opp_data["AccountId"] = account_id

            if id:
                sf.Opportunity.update(id, opp_data)
            else:
                sf.Opportunity.create(opp_data)
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_opportunity(id):
        try:
            sf.Opportunity.delete(id)
            return True, None
        except Exception as e:
            return False, str(e)

    def normalize_keys(record):
        return {
            "id": record.get("Id"),
            "name": record.get("Name", ""),
            "account_id": record.get("AccountId", ""),
            "account_name": record.get("AccountName", ""),
            "stage": record.get("StageName", ""),
            "close_date": record.get("CloseDate", ""),
            "amount": record.get("Amount", ""),
            "probability": record.get("Probability", ""),
            "opp_type": record.get("Type", ""),
            "lead_source": record.get("LeadSource", ""),
            "next_step": record.get("NextStep", ""),
            "description": record.get("Description", ""),
            "forecast_category": record.get("ForecastCategoryName", "")
        }

    # ------------------- FORM BUILDER -------------------
    def build_opportunity_fields(prefix="new", opp=None, accounts=[]):
        if opp is None:
            opp = {}

        col_outer, spacer = st.columns([2, 1])
        with col_outer:
            col1, col2 = st.columns([2, 2])

            with col1:
                name = st.text_input("Opportunity Name", value=opp.get("name", ""), key=f"name_{prefix}")

                # Account dropdown
                account_options = [""] + [f"{a['Name']} ({a['Id']})" for a in accounts]
                selected_account = f"{opp.get('account_name','')} ({opp.get('account_id','')})" if opp.get("account_id") else ""
                account_choice = st.selectbox("Account (Parent)", account_options,
                                              index=account_options.index(selected_account) if selected_account in account_options else 0,
                                              key=f"account_{prefix}")
                account_id = account_choice.split("(")[-1].replace(")", "").strip() if "(" in account_choice else ""

                # Stage
                stage_options = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition",
                                 "Id. Decision Makers", "Perception Analysis", "Proposal/Price Quote",
                                 "Negotiation/Review", "Closed Won", "Closed Lost"]
                stage_index = stage_options.index(opp.get("stage", "")) if opp.get("stage", "") in stage_options else 0
                stage = st.selectbox("Stage", stage_options, index=stage_index, key=f"stage_{prefix}")

                close_date = st.date_input("Close Date",
                                           value=pd.to_datetime(opp.get("close_date", pd.Timestamp.today())),
                                           key=f"close_{prefix}")

                next_step = st.text_input("Next Step", value=opp.get("next_step", ""), key=f"next_{prefix}")

            with col2:
                amount = st.number_input("Amount", value=float(opp.get("amount", 0) or 0), step=100.0, key=f"amount_{prefix}")
                probability = st.number_input("Probability (%)", value=float(opp.get("probability", 0) or 0), step=1.0, key=f"prob_{prefix}")

                type_options = ["", "New Customer", "Existing Customer - Upgrade", "Existing Customer - Replacement", "Existing Customer - Downgrade"]
                type_index = type_options.index(opp.get("opp_type", "")) if opp.get("opp_type", "") in type_options else 0
                opp_type = st.selectbox("Type", type_options, index=type_index, key=f"type_{prefix}")

                lead_source_options = ["", "Web", "Phone Inquiry", "Partner Referral", "Purchased List", "Other"]
                ls_index = lead_source_options.index(opp.get("lead_source", "")) if opp.get("lead_source", "") in lead_source_options else 0
                lead_source = st.selectbox("Lead Source", lead_source_options, index=ls_index, key=f"lead_{prefix}")

                forecast_options = ["", "Pipeline", "Best Case", "Commit", "Closed", "Omitted"]
                fc_index = forecast_options.index(opp.get("forecast_category", "")) if opp.get("forecast_category", "") in forecast_options else 0
                forecast_category = st.selectbox("Forecast Category", forecast_options, index=fc_index, key=f"forecast_{prefix}")

            description = st.text_area("Description", value=opp.get("description", ""), key=f"desc_{prefix}")

        return {
            "name": name,
            "account_id": account_id,
            "stage": stage,
            "close_date": str(close_date),
            "amount": amount,
            "probability": probability,
            "opp_type": opp_type,
            "lead_source": lead_source,
            "next_step": next_step,
            "description": description,
            "forecast_category": forecast_category
        }

    # ------------------- MAIN TABS -------------------
    tab1, tab2 = st.tabs(["🔍 Search / Edit Opportunities", "➕ Add New Opportunity"])

    # ------------------- TAB 1: SEARCH / EDIT -------------------
    with tab1:
        st.markdown("<h4 style='color:#FF8800;'>Search Opportunities</h4>", unsafe_allow_html=True)
        search_name = st.text_input("Enter Name to search", placeholder="e.g. ACME Deal")

        if search_name:
            results = search_opportunities(search_name)
            if results:
                st.success(f"✅ Found {len(results)} record(s)")
                df = pd.DataFrame(results).drop(columns=["attributes"], errors="ignore")
                st.dataframe(df, use_container_width=True)

                options = [f"{r['Name']} | {r.get('StageName','')} | {r.get('Amount','')}" for r in results]
                st.markdown("<h5 style='color:#FF8800; margin-bottom:-10px;'>Select record to edit</h5>", unsafe_allow_html=True)
                selected_idx = st.selectbox("", range(len(results)), format_func=lambda x: options[x])
                record_to_edit = normalize_keys(results[selected_idx])

                accounts = sf.query("SELECT Id, Name FROM Account LIMIT 200")['records']
                with st.form(f"edit_form_{record_to_edit['id']}", clear_on_submit=False):
                    updated_data = build_opportunity_fields(prefix=f"edit_{record_to_edit['id']}", opp=record_to_edit, accounts=accounts)
                    updated_data["id"] = record_to_edit["id"]

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        submitted_update = st.form_submit_button("💾 Update Record")
                        if submitted_update:
                            success, err = upsert_opportunity(**updated_data)
                            if success:
                                st.success("✅ Record updated successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Update failed: {err}")

                    with col2:
                        confirm_delete = st.checkbox("Confirm delete", key=f"confirm_delete_{record_to_edit['id']}")
                        delete_clicked = st.form_submit_button("🗑️ Delete Record")
                        if delete_clicked:
                            if confirm_delete:
                                success, err = delete_opportunity(record_to_edit["id"])
                                if success:
                                    st.warning("⚠️ Record deleted successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Delete failed: {err}")
                            else:
                                st.warning("⚠️ Please confirm delete before proceeding.")

    # ------------------- TAB 2: ADD NEW -------------------
    with tab2:
        st.markdown("<h4 style='color:#FF8800;'>Add New Opportunity</h4>", unsafe_allow_html=True)
        accounts = sf.query("SELECT Id, Name FROM Account LIMIT 200")['records']

        with st.form("new_opp_form", clear_on_submit=True):
            new_opp = build_opportunity_fields(prefix="new", accounts=accounts)
            submitted_new = st.form_submit_button("💾 Save New Opportunity")

            if submitted_new:
                if new_opp["name"] and new_opp["account_id"]:
                    success, err = upsert_opportunity(id=None, **new_opp)
                    if success:
                        st.success("✅ Record added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add record: {err}")
                else:
                    st.warning("⚠️ Please enter Opportunity Name and select an Account before saving.")
