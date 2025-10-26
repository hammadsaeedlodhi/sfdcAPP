import streamlit as st
import pandas as pd
import time


def run():
    # --- HEADER ---
    st.markdown(
        "<h3 style='color: orange;'>👤 Salesforce Contact Management</h3>",
        unsafe_allow_html=True
    )
    st.write("You can search, add, edit, delete, or bulk upload Contact records (duplicates skipped automatically).")

    sf = st.session_state.sf_connection

    # --- Helper: Load Accounts for lookup ---
    def load_accounts_for_lookup(limit=500):
        try:
            q = f"SELECT Id, Name FROM Account ORDER BY Name LIMIT {limit}"
            res = sf.query(q)['records']
            return [(r.get('Id'), r.get('Name')) for r in res]
        except Exception:
            return []

    # --- Helper: Get existing contact keys (for duplicate check) ---
    def get_existing_contacts_keys():
        try:
            q = "SELECT FirstName, LastName, Email FROM Contact"
            res = sf.query_all(q)['records']
            keys = set()
            for r in res:
                fname = (r.get("FirstName") or "").strip().lower()
                lname = (r.get("LastName") or "").strip().lower()
                email = (r.get("Email") or "").strip().lower()
                key = f"{fname}|{lname}|{email}"
                keys.add(key)
            return keys
        except Exception as e:
            st.error(f"⚠️ Could not fetch existing Contacts: {e}")
            return set()

    # --- Salesforce CRUD ---
    def search_contacts(name_search):
        try:
            query = f"""
                SELECT Id, FirstName, LastName, Phone, Email, Title, Department, MailingCountry, LeadSource,
                       AccountId, Account.Name
                FROM Contact
                WHERE FirstName LIKE '%{name_search}%' OR LastName LIKE '%{name_search}%'
                LIMIT 100
            """
            results = sf.query(query)['records']
            return results
        except Exception as e:
            st.error(f"❌ Salesforce Query Error: {e}")
            return []

    def upsert_contact(id=None, first_name="", last_name="", phone="", email="", title="", department="", country="", lead_source="", account_id=None):
        try:
            data = {
                "FirstName": first_name,
                "LastName": last_name,
                "Phone": phone,
                "Email": email,
                "Title": title,
                "Department": department,
                "MailingCountry": country,
                "LeadSource": lead_source,
            }
            if account_id:
                data["AccountId"] = account_id

            if id:
                sf.Contact.update(id, data)
            else:
                sf.Contact.create(data)
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_contact(id):
        try:
            sf.Contact.delete(id)
            return True, None
        except Exception as e:
            return False, str(e)

    def normalize_keys(record):
        account_obj = record.get("Account") or {}
        return {
            "id": record.get("Id"),
            "first_name": record.get("FirstName", ""),
            "last_name": record.get("LastName", ""),
            "phone": record.get("Phone", ""),
            "email": record.get("Email", ""),
            "title": record.get("Title", ""),
            "department": record.get("Department", ""),
            "country": record.get("MailingCountry", ""),
            "lead_source": record.get("LeadSource", ""),
            "account_id": record.get("AccountId"),
            "account_name": account_obj.get("Name", "") if isinstance(account_obj, dict) else ""
        }

    # --- FORM BUILDER ---
    def build_contact_fields_left_aligned(prefix="new", contact=None, accounts_lookup=None):
        if contact is None:
            contact = {}
        if accounts_lookup is None:
            accounts_lookup = []

        account_options = [("", "")] + accounts_lookup
        account_display = [f"{name} ({aid})" if name else "" for (aid, name) in account_options]

        col1, col2, col3 = st.columns(3)

        with col1:
            first_name = st.text_input("First Name", value=contact.get("first_name", ""), key=f"fname_{prefix}")
            last_name = st.text_input("Last Name", value=contact.get("last_name", ""), key=f"lname_{prefix}")
            title = st.text_input("Title", value=contact.get("title", ""), key=f"title_{prefix}")

        with col2:
            phone = st.text_input("Phone", value=contact.get("phone", ""), key=f"phone_{prefix}")
            email = st.text_input("Email", value=contact.get("email", ""), key=f"email_{prefix}")
            department = st.text_input("Department", value=contact.get("department", ""), key=f"dept_{prefix}")

        with col3:
            country = st.text_input("Country", value=contact.get("country", ""), key=f"country_{prefix}")
            LeadSource = ["", "Web", "Phone Inquiry", "Partner Referral", "Purchased List", "Other"]
            lead_source_index = LeadSource.index(contact.get("lead_source", "")) if contact.get("lead_source", "") in LeadSource else 0
            lead_source = st.selectbox("Lead Source", LeadSource, index=lead_source_index, key=f"lead_{prefix}")

            current_account_id = contact.get("account_id") or ""
            idx = 0
            for i, (aid, _) in enumerate(account_options):
                if aid == current_account_id:
                    idx = i
                    break
            selected_display = st.selectbox("Account (Parent)", account_display, index=idx, key=f"account_{prefix}")
            selected_account_id = account_options[account_display.index(selected_display)][0] if selected_display in account_display else ""

        return {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "email": email,
            "title": title,
            "department": department,
            "country": country,
            "lead_source": lead_source,
            "account_id": selected_account_id
        }

    # --- TABS ---
    accounts_lookup = load_accounts_for_lookup()
    tab1, tab2, tab3 = st.tabs(["🔍 Search & Edit Contacts", "➕ Create New Contact", "📤 Bulk Upload Contacts"])

    # --- TAB 1: SEARCH & EDIT ---
    with tab1:
        st.markdown("<h4 style='color: orange;'>🔍 Search Contacts by Name</h4>", unsafe_allow_html=True)
        search_name = st.text_input("Enter First or Last Name to search", label_visibility="collapsed")

        if search_name:
            results = search_contacts(search_name)
            if results:
                st.success(f"✅ Found {len(results)} record(s)")
                df = pd.DataFrame(results).drop(columns=["attributes"], errors="ignore")
                st.dataframe(df, use_container_width=True)

                options = [
                    f"{r.get('FirstName','')} {r.get('LastName','')} | {r.get('Email','')} | {r.get('Phone','')}"
                    for r in results
                ]
                selected_idx = st.selectbox(
                    "Select record to edit",
                    range(len(results)),
                    format_func=lambda x: options[x]
                )
                record_to_edit = normalize_keys(results[selected_idx])

                st.markdown("<h4 style='color: orange;'>✏️ Edit Contact</h4>", unsafe_allow_html=True)
                with st.form(f"edit_form_{record_to_edit['id']}"):
                    updated_data = build_contact_fields_left_aligned(
                        prefix=f"edit_{record_to_edit['id']}",
                        contact=record_to_edit,
                        accounts_lookup=accounts_lookup
                    )
                    updated_data["id"] = record_to_edit["id"]

                    col_btn1, col_btn2, _ = st.columns([1, 1, 3])
                    with col_btn1:
                        update_click = st.form_submit_button("💾 Update", use_container_width=True)
                    with col_btn2:
                        delete_click = st.form_submit_button("🗑️ Delete", use_container_width=True)

                    confirm_delete = st.checkbox("Confirm delete", key=f"confirm_del_{record_to_edit['id']}")

                    if update_click:
                        ok, err = upsert_contact(**updated_data)
                        if ok:
                            st.success("✅ Contact updated successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Update failed: {err}")

                    if delete_click:
                        if confirm_delete:
                            ok, err = delete_contact(record_to_edit["id"])
                            if ok:
                                st.warning("⚠️ Contact deleted successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Delete failed: {err}")
                        else:
                            st.warning("⚠️ Please confirm before deleting.")

    # --- TAB 2: CREATE NEW ---
    with tab2:
        st.markdown("<h4 style='color: orange;'>➕ Add New Contact</h4>", unsafe_allow_html=True)
        with st.form("new_contact_form", clear_on_submit=True):
            new_contact = build_contact_fields_left_aligned(prefix="new", accounts_lookup=accounts_lookup)
            submitted_new = st.form_submit_button("Save New Contact", use_container_width=True)

            if submitted_new:
                if new_contact["last_name"]:
                    ok, err = upsert_contact(**new_contact)
                    if ok:
                        st.success("✅ Contact added successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add contact: {err}")
                else:
                    st.warning("⚠️ Please enter Last Name before saving.")

    # --- TAB 3: BULK UPLOAD ---
    with tab3:
        st.markdown("<h4 style='color: orange;'>📤 Bulk Upload Contacts (Avoid Duplicates)</h4>", unsafe_allow_html=True)
        st.info("Upload Excel/CSV. Existing contacts (First+Last+Email) will be skipped automatically.")

        file = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

        if file:
            try:
                df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
                st.write("✅ File Uploaded Successfully. Preview below:")
                st.dataframe(df.head(), use_container_width=True)

                df.columns = df.columns.str.strip()
                needed = ["FirstName", "LastName", "Email"]
                missing = [x for x in needed if x not in df.columns]
                if missing:
                    st.warning(f"⚠️ Missing required columns: {', '.join(missing)}")
                else:
                    st.success(f"✅ {len(df)} records ready. Checking for duplicates...")

                    with st.spinner("Fetching existing contacts..."):
                        existing_keys = get_existing_contacts_keys()

                    df["__key__"] = df.apply(
                        lambda r: f"{str(r.get('FirstName','')).strip().lower()}|{str(r.get('LastName','')).strip().lower()}|{str(r.get('Email','')).strip().lower()}",
                        axis=1
                    )
                    df_unique = df[~df["__key__"].isin(existing_keys)].drop(columns="__key__")

                    skipped = len(df) - len(df_unique)
                    st.info(f"🧾 {skipped} duplicates skipped, {len(df_unique)} new to insert.")

                    if len(df_unique) > 0:
                        if st.button("🚀 Insert New Contacts"):
                            with st.spinner("Rechecking duplicates before inserting..."):
                                latest = get_existing_contacts_keys()
                                df_unique["__key__"] = df_unique.apply(
                                    lambda r: f"{str(r.get('FirstName','')).strip().lower()}|{str(r.get('LastName','')).strip().lower()}|{str(r.get('Email','')).strip().lower()}",
                                    axis=1
                                )
                                df_final = df_unique[~df_unique["__key__"].isin(latest)].drop(columns="__key__")

                            if df_final.empty:
                                st.warning("⚠️ All records already exist — nothing to insert.")
                            else:
                                try:
                                    records = df_final.to_dict(orient="records")
                                    batch_size = 200
                                    success_count = 0
                                    fail_count = 0

                                    for i in range(0, len(records), batch_size):
                                        batch = records[i:i + batch_size]
                                        try:
                                            results = sf.bulk.Contact.insert(batch)
                                            for r in results:
                                                if r.get("success"):
                                                    success_count += 1
                                                else:
                                                    fail_count += 1
                                        except Exception as e:
                                            st.error(f"Error inserting batch: {e}")
                                            fail_count += len(batch)

                                    st.success(f"✅ Upload complete! {success_count} inserted, {fail_count} failed.")
                                except Exception as e:
                                    st.error(f"❌ Bulk insert failed: {e}")
                    else:
                        st.warning("⚠️ No new records to insert — all were duplicates.")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
