import streamlit as st
import pandas as pd
import time

def run():
    st.markdown(
        "<h2 style='text-align:left; color:#FF8800;'>💼 Salesforce Opportunity Manager</h2>",
        unsafe_allow_html=True
    )
    st.write("Use this app to search, add, edit, delete, or bulk upload Opportunity records in Salesforce.")

    sf = st.session_state.sf_connection

    # ------------------- CRUD OPERATIONS -------------------
    def search_opportunities(name_search):
        try:
            query = f"""
                SELECT Id, Name, Account.Id, Account.Name, StageName, CloseDate, Amount, Probability, Type,
                       LeadSource, NextStep, Description, ForecastCategoryName
                FROM Opportunity
                WHERE Name LIKE '%{name_search}%'
                
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

                account_options = [""] + [f"{a['Name']} ({a['Id']})" for a in accounts]
                selected_account = f"{opp.get('account_name','')} ({opp.get('account_id','')})" if opp.get("account_id") else ""
                account_choice = st.selectbox("Account (Parent)", account_options,
                                              index=account_options.index(selected_account) if selected_account in account_options else 0,
                                              key=f"account_{prefix}")
                account_id = account_choice.split("(")[-1].replace(")", "").strip() if "(" in account_choice else ""

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

    # ------------------- BULK UPLOAD -------------------
    def bulk_upload(file):
        df = pd.read_excel(file)
        st.success(f"✅ File Uploaded Successfully. Preview below:")
        st.dataframe(df.head(), use_container_width=True)

        if 'Name' not in df.columns:
            st.error("❌ Excel must contain a 'Name' column.")
            return

        # 🔹 Convert CloseDate column to proper Salesforce format (YYYY-MM-DD)
        if 'CloseDate' in df.columns:
            try:
                df['CloseDate'] = pd.to_datetime(df['CloseDate'], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')
            except Exception:
                st.warning("⚠️ Could not convert some CloseDate values — please verify format in Excel.")

        st.info(f"✅ {len(df)} records ready. Checking for duplicates...")
        existing = sf.query_all("SELECT Name FROM Opportunity")['records']
        existing_names = {e['Name'] for e in existing}

        new_records = df[~df['Name'].isin(existing_names)]
        duplicates = df[df['Name'].isin(existing_names)]

        st.write(f"🧾 {len(duplicates)} duplicates skipped, {len(new_records)} new to insert.")

        if len(new_records) == 0:
            st.warning("⚠️ No new records to insert.")
            return

        if st.button("🚀 Insert Opportunities"):
            total = len(new_records)
            batch_size = 100
            progress = st.progress(0)
            inserted_count = 0
            failed_count = 0

            for i in range(0, total, batch_size):
                batch = new_records.iloc[i:i+batch_size]
                for _, row in batch.iterrows():
                    try:
                        sf.Opportunity.create({
                            "Name": row["Name"],
                            "StageName": row.get("StageName", "Prospecting"),
                            "CloseDate": row.get("CloseDate", str(pd.Timestamp.today().date())),
                            "AccountId": row.get("AccountId", None),
                            "Amount": row.get("Amount", None),
                            "Probability": row.get("Probability", None),
                            "Type": row.get("Type", None),
                            "LeadSource": row.get("LeadSource", None),
                            "NextStep": row.get("NextStep", None),
                            "Description": row.get("Description", None),
                            "ForecastCategoryName": row.get("ForecastCategoryName", None)
                        })
                        inserted_count += 1
                    except Exception:
                        failed_count += 1

                progress.progress(min((i + batch_size) / total, 1.0))
                st.write(f"📦 Processed batch {i//batch_size + 1} of {total//batch_size + 1}...")

            st.success(f"✅ Upload complete! {inserted_count} inserted, {failed_count} failed.")

    # ------------------- TABS -------------------
    tab1, tab2, tab3 = st.tabs([
        "🔍 Search / Edit Opportunities",
        "➕ Add New Opportunity",
        "📤 Upload from Excel"
    ])

    # --- TAB 1: Search & Edit ---
    with tab1:
        st.markdown("<h4 style='color:#FF8800;'>Search Opportunities</h4>", unsafe_allow_html=True)
        search_name = st.text_input("Enter Opportunity Name to search")

        if search_name:
            results = search_opportunities(search_name)
            if results:
                st.success(f"✅ Found {len(results)} record(s)")
                df = pd.DataFrame(results).drop(columns=["attributes"], errors="ignore")
                st.dataframe(df, use_container_width=True)

                options = [f"{r['Name']} | {r.get('StageName','')} | {r.get('Amount','')}" for r in results]
                selected_idx = st.selectbox("Select record to edit", range(len(results)), format_func=lambda x: options[x])
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

    # --- TAB 2: Add New Opportunity ---
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

    # --- TAB 3: Bulk Upload ---
    with tab3:
        st.markdown("<h4 style='color:#FF8800;'>📤 Upload Opportunities from Excel</h4>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload an Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file:
            bulk_upload(uploaded_file)
