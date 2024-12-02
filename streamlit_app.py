import streamlit as st
import random
import pandas as pd
import os
from datetime import date, timedelta

# Path to the Excel file
EXCEL_FILE = "user_accounts.xlsx"

# Initialize user accounts in session state
if "user_accounts" not in st.session_state:
    st.session_state.user_accounts = {}

if "current_account" not in st.session_state:
    st.session_state.current_account = None

# Function to generate unique bank account number
def generate_bank_account():
    prefix = "630"
    middle = str(random.randint(0, 999)).zfill(3)
    end = str(random.randint(0, 999)).zfill(3)
    return f"{prefix}-{middle}-{end}"

# Function to load user data from Excel
def load_user_data():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        user_data = df.set_index("account_number").to_dict(orient="index")

        # Ensure 'mutasi' is a list for all users
        for account_number, account_info in user_data.items():
            if isinstance(account_info['mutasi'], str):
                account_info['mutasi'] = [account_info['mutasi']]
            elif account_info['mutasi'] is None:
                account_info['mutasi'] = []

        return user_data
    return {}

# Function to ensure mutasi is a list before appending
def ensure_mutasi_is_list(account_number):
    account_data = st.session_state.user_accounts[account_number]
    if isinstance(account_data['mutasi'], str):
        account_data['mutasi'] = [account_data['mutasi']]
    elif account_data['mutasi'] is None:
        account_data['mutasi'] = []

# Function to save user data to Excel
def save_user_data():
    try:
        user_data = st.session_state.user_accounts

        # Ensure mutasi is always a list
        for account_number, account_info in user_data.items():
            if isinstance(account_info['mutasi'], str):
                account_info['mutasi'] = []

        df = pd.DataFrame.from_dict(user_data, orient="index")

        # Save the file (create if it doesn't exist)
        df.to_excel(EXCEL_FILE, index_label="account_number", engine='openpyxl')

    except PermissionError:
        st.error("Permission denied: Cannot save to the file. Please close any programs using the file or check file permissions.")
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Main Menu
def main_menu():
    st.title("_Selamat datang_ di :orange[Equi]:blue[Trust] :green[Finance]!")

    menu = st.sidebar.radio("Pilih Menu:", ["Transaksi Bank", "Mutasi Rekening", "Pembukaan Rekening", "Bantuan"])

    if menu == "Transaksi Bank":
        bank_transactions()
    elif menu == "Mutasi Rekening":
        account_statement()
    elif menu == "Pembukaan Rekening":
        create_account()
    elif menu == "Bantuan":
        show_help()

# Create a New Account
def create_account():
    st.title("Pembukaan Rekening Baru")

    with st.form("create_account_form"):
        user = st.text_input("Nama lengkap:")
        today = date.today()
        min_date = today - timedelta(days = 100 * 365)
        dob = st.date_input("Tanggal lahir (YYYY-MM-DD):", value = today, min_value = min_date)
        address = st.text_area("Alamat:")
        nik = st.text_input("Nomor NIK:")
        password = st.text_input("Buat password:", type="password")
        submitted = st.form_submit_button("Buka Rekening")

    if submitted:
        if user and dob and address and nik and password:
            account_number = generate_bank_account()
            st.session_state.user_accounts[account_number] = {
                "nama": user,
                "dob": dob,
                "alamat": address,
                "nik": nik,
                "password": password,
                "saldo": 0,
                "mutasi": []
            }
            save_user_data()
            st.success(f"Rekening berhasil dibuat! Nomor rekening Anda: {account_number}")
        else:
            st.error("Semua kolom wajib diisi!")

# Bank Transactions
def bank_transactions():
    st.title("Transaksi Bank")

    if st.session_state.current_account:
        account_number = st.session_state.current_account
    else:
        # Form for account login
        with st.form("login_form"):
            account_number = st.text_input("Masukkan nomor rekening:")
            pin = st.text_input("Masukkan PIN:", type="password")
            login_submitted = st.form_submit_button("Masuk")

        if login_submitted:
            if account_number in st.session_state.user_accounts and st.session_state.user_accounts[account_number]["password"] == pin:
                st.success(f"Selamat datang, {st.session_state.user_accounts[account_number]['nama']}!")
                st.session_state.current_account = account_number
            else:
                st.error("Nomor rekening atau PIN salah.")

    if st.session_state.current_account:
        ensure_mutasi_is_list(account_number)
        transaction_menu(st.session_state.current_account)

# Submenu for transactions
def transaction_menu(account_number):
    transaction_option = st.radio("Pilih transaksi:", ["Lihat Saldo", "Setor Uang", "Transfer", "Keluar"])

    if transaction_option == "Lihat Saldo":
        st.write(f"Saldo Anda: Rp{st.session_state.user_accounts[account_number]['saldo']}")

    elif transaction_option == "Setor Uang":
        deposit_amount = st.number_input("Masukkan jumlah setoran (Rp):", min_value=0)
        if st.button("Setor"):
            ensure_mutasi_is_list(account_number)
            st.session_state.user_accounts[account_number]['saldo'] += deposit_amount
            st.session_state.user_accounts[account_number]['mutasi'].append(f"Setoran: +Rp{deposit_amount}")
            save_user_data()
            st.success(f"Berhasil menyetor Rp{deposit_amount}. Saldo baru: Rp{st.session_state.user_accounts[account_number]['saldo']}")

    elif transaction_option == "Transfer":
        transfer_account = st.text_input("Nomor rekening tujuan:")
        transfer_amount = st.number_input("Jumlah transfer (Rp):", min_value=0)
        if st.button("Transfer"):
            if transfer_account in st.session_state.user_accounts:
                if st.session_state.user_accounts[account_number]['saldo'] >= transfer_amount:
                    # Update saldo pengirim dan penerima
                    st.session_state.user_accounts[account_number]['saldo'] -= transfer_amount
                    st.session_state.user_accounts[transfer_account]['saldo'] += transfer_amount
                    
                    # Pastikan mutasi pada kedua rekening diperbarui
                    ensure_mutasi_is_list(account_number)
                    ensure_mutasi_is_list(transfer_account)

                    # Menambahkan transaksi pada mutasi
                    st.session_state.user_accounts[account_number]['mutasi'].append(f"Transfer keluar: -Rp{transfer_amount} ke {transfer_account}")
                    st.session_state.user_accounts[transfer_account]['mutasi'].append(f"Transfer masuk: +Rp{transfer_amount} dari {account_number}")
                    
                    # Simpan data setelah update
                    save_user_data()

                    st.success(f"Berhasil mentransfer Rp{transfer_amount} ke {transfer_account}.")
                else:
                    st.error("Saldo tidak mencukupi!")
            else:
                st.error("Nomor rekening tujuan tidak ditemukan.")


    elif transaction_option == "Keluar":
        st.info("Anda telah keluar dari menu transaksi.")
        st.session_state.current_account = None

# Account Statement (Mutasi Rekening)
def account_statement():
    st.title("Mutasi Rekening")

    with st.form("statement_form"):
        account_number = st.text_input("Masukkan nomor rekening:")
        pin = st.text_input("Masukkan PIN:", type="password")
        statement_submitted = st.form_submit_button("Lihat Mutasi")

    if statement_submitted:
        if account_number in st.session_state.user_accounts and st.session_state.user_accounts[account_number]["password"] == pin:
            st.success(f"Riwayat Mutasi Rekening {account_number}:")
            mutasi = st.session_state.user_accounts[account_number]["mutasi"]
            if mutasi:
                for transaksi in mutasi:
                    st.write(transaksi)
            else:
                st.write("Belum ada riwayat transaksi.")
        else:
            st.error("Nomor rekening atau PIN salah.")

# Help Page
import streamlit as st

# Dictionary of FAQs and their responses
faq_data = {
    "pembukaan rekening baru": """\
Untuk membuka rekening baru:
1. Masuk ke menu **Pembukaan Rekening**.
2. Isi data seperti nama lengkap, tanggal lahir, alamat, NIK, dan password.
3. Nomor rekening Anda akan dibuat otomatis setelah data dikonfirmasi.""",
    "lupa nomor rekening": "Jika Anda lupa nomor rekening, silakan hubungi layanan pelanggan di support@equitrustfinance.com atau +62 123 456 789.",
    "cara setor uang": """\
Untuk menyetor uang:
1. Login ke menu **Transaksi Bank**.
2. Pilih opsi **Setor Uang**.
3. Masukkan jumlah uang dan tekan tombol **Setor**.
4. Saldo Anda akan bertambah secara otomatis.""",
    "cara transfer uang": """\
Untuk mentransfer uang:
1. Login ke menu **Transaksi Bank**.
2. Pilih opsi **Transfer**.
3. Masukkan nomor rekening tujuan dan jumlah transfer.
4. Pastikan saldo Anda mencukupi sebelum mengonfirmasi transfer.""",
    "lihat saldo": """\
Untuk melihat saldo:
1. Login ke menu **Transaksi Bank**.
2. Pilih opsi **Lihat Saldo**.
3. Saldo rekening Anda akan ditampilkan di layar.""",
    "keamanan rekening": """\
Tips keamanan rekening:
1. Jangan bagikan PIN/password kepada siapa pun.
2. Gunakan password yang kuat.
3. Selalu logout setelah selesai.
4. Waspadai penipuan yang meminta informasi pribadi Anda.""",
    "hubungi layanan pelanggan": """\
Anda dapat menghubungi layanan pelanggan melalui:
- **Email**: support@equitrustfinance.com
- **Telepon**: +62 123 456 789
- **Jam Operasional**: Senin - Jumat, 08.00 - 17.00 WIB.""",
}

import streamlit as st
import time
from difflib import get_close_matches

# Data FAQ
faq_data = {
    "buka rekening": "Tentu! Untuk membuka rekening baru, pilih menu **Pembukaan Rekening** dan isi data yang diminta. Jangan ragu jika ada kesulitan, ya!",
    "setor uang": "Oh, mudah sekali! Masuk ke menu **Transaksi Bank**, pilih opsi **Setor Uang**, masukkan jumlah yang ingin disetor, dan konfirmasi.",
    "transfer uang": "Untuk transfer uang, masuk ke menu **Transaksi Bank**, pilih **Transfer**, masukkan nomor rekening tujuan dan jumlah transfer, lalu konfirmasi.",
    "lihat saldo": "Ingin tahu saldo Anda? Pilih menu **Transaksi Bank**, lalu klik **Lihat Saldo** untuk melihatnya.",
    "keamanan rekening": "Pastikan untuk menjaga keamanan rekening Anda! Jangan bagikan PIN atau password kepada siapa pun, dan selalu logout setelah selesai.",
    "hubungi layanan pelanggan": "Kami di sini untuk membantu! Hubungi kami di support@equitrustfinance.com atau telepon +62 123 456 789 jika ada masalah."
}

# Fungsi pencocokan cerdas
def get_response(user_query):
    normalized_query = user_query.lower().strip()
    matched_keywords = get_close_matches(normalized_query, faq_data.keys(), n=1, cutoff=0.3)
    
    # Respons sesuai konteks bank
    if matched_keywords:
        return faq_data[matched_keywords[0]]
    
    # Respons untuk pertanyaan di luar konteks
    if "hai" in normalized_query or "halo" in normalized_query:
        return "Hai juga! Apa kabar? Ada yang bisa saya bantu? 😊"
    elif "terima kasih" or "makasih" in normalized_query:
        return "Sama-sama! Senang bisa membantu. Kalau ada lagi yang dibutuhkan, tinggal tanya saja. 😄"
    elif "apa kabar" in normalized_query:
        return "Aku baik-baik saja! Terima kasih sudah bertanya. Semoga kamu juga dalam keadaan baik! 🌟"
    elif "pembuat" in normalized_query: 
        return "Pembuat saya adalah Nathaniel Lemuel Chandra, jika Anda tertarik ingin mengetahuinya lebih lanjut silahkan kontak: 0895-0666-7884"
    else:
        return "Hmm, aku belum punya jawaban untuk itu. Tapi aku selalu belajar! Coba tanyakan dengan kata lain, ya. 😊"

# Fungsi animasi mengetik
def typing_animation(message, delay=0.05):
    placeholder = st.empty()
    displayed_message = ""
    for char in message:
        displayed_message += char
        placeholder.markdown(f":robot_face: : :red[{displayed_message}]")  # Text in red
        time.sleep(delay)
    placeholder.markdown(f":robot_face: : :red[{displayed_message}]")  # Final message in red

# Halaman chatbot
def show_help():
    st.title(":orange[Equi]:blue[Trust] _:red[AI] Assistant_ :robot_face: ")

    # Inisialisasi percakapan
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Kolom percakapan
    st.markdown(":robot_face: : :red[Hai, ada yang bisa saya bantu?] ")
    chat_placeholder = st.container()

    # Tampilkan percakapan sebelumnya
    with chat_placeholder:
        for sender, message in st.session_state.conversation:
            if sender == "user":
                st.markdown(f"**Anda:** {message}")
            elif sender == "bot":
                st.markdown(f"**:robot_face: :** :red[{message}]")  # Bot message in red

    # Kolom untuk memastikan input tetap di bawah
    user_query = st.text_input("Tulis pertanyaan Anda di sini:", key="user_input", placeholder="Misalnya: Bagaimana cara transfer uang?", label_visibility="collapsed")

    # Proses pesan
    if user_query:
        if st.button("Kirim") or st.session_state.get("user_input"):
            # Simpan pertanyaan pengguna
            st.session_state.conversation.append(("user", user_query))

            # Cari respons dari AI
            response = get_response(user_query)

            # Tambahkan respons bot ke percakapan
            st.session_state.conversation.append(("bot", response))

            # Tampilkan respons dengan animasi hanya untuk pesan baru
            with chat_placeholder:
                st.markdown(f"**Anda:** {user_query}")
                typing_animation(response)  # Animate the bot's response


if __name__== "__main__":
    st.session_state.user_accounts = load_user_data()
    main_menu()
