import logging
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import os
from googleapiclient.errors import HttpError

# Configuration
app = Flask(__name__)
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]
# Identifiants Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1SQM-LgJnOTAmovr6hjMVFJaxq8B6gLgiOohxK3LBgGE'  # Remplacez par l'ID de votre Google Sheet
RANGE_NAME = 'Paiements!A1:Z1'  # Changez en fonction de votre feuille et de la plage voulue

# Configurez le logger
logging.basicConfig(level=logging.DEBUG)  # Niveau de log DEBUG pour capturer plus d'informations
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
TYPE = os.environ.get("TYPE")
PROJECT_ID = os.environ.get("PROJECT_ID")
PRIVATE_KEY_ID = os.environ.get("PRIVATE_KEY_ID")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY").replace("\\n", "\n")
CLIENT_EMAIL = os.environ.get("CLIENT_EMAIL")
CLIENT_ID = os.environ.get("CLIENT_ID")
AUTH_URI = os.environ.get("AUTH_URI")
TOKEN_URI = os.environ.get("TOKEN_URI")
AUTH_PROVIDER_X509_CERT_URL = os.environ.get("AUTH_PROVIDER_X509_CERT_URL")
CLIENT_X509_CERT_URL = os.environ.get("CLIENT_X509_CERT_URL")

# Créez des identifiants à partir du fichier credentials.json
creds = ServiceAccountCredentials.from_json_keyfile_dict({
    "type": TYPE,
    "project_id": PROJECT_ID,
    "private_key_id": PRIVATE_KEY_ID,
    "private_key": PRIVATE_KEY,
    "client_email": CLIENT_EMAIL,
    "client_id": CLIENT_ID,
    "auth_uri": AUTH_URI,
    "token_uri": TOKEN_URI,
    "auth_provider_x509_cert_url": AUTH_PROVIDER_X509_CERT_URL,
    "client_x509_cert_url": CLIENT_X509_CERT_URL
}, scope)

@app.route('/webhook', methods=['POST', 'GET'])  # Accepter POST et GET si nécessaire
def webhook():
    # Récupération des paramètres de la requête
    if request.method == 'POST':
        data = request.form
    else:
        data = request.args

    print(f"Webhook reçu : {data}")  # Afficher les détails du webhook dans la console
    logger.debug(f"Requête reçue : {data}")  # Log de la requête

    try:
        # Extraire les données de la requête
        client_fullname = data.get('client_fullname', '').title()
        trans_amount = data.get('trans_amount')

        # Déterminer la valeur correspondante pour trans_amount
        pack_name = ''
        if trans_amount == '179':
            pack_name = 'Pack Fréquence'
        elif trans_amount == '249':
            pack_name = 'Pack Cartographie Avancée'
        elif trans_amount == '499':
            pack_name = 'Pack Protection & Résonance'
        else:
            pack_name = 'Autre Pack'

        # Extraire les données de la requête
        row_data = [
            data.get('trans_date'),
            client_fullname,
            data.get('client_email'),
            data.get('client_phone'),
            trans_amount,
            pack_name,
            data.get('reply_desc'),
            data.get('trans_id')
        ]

        logger.debug(f"Données à insérer : {row_data}")  # Log des données extraites

        # Ajouter les données dans le Google Sheet
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        body = {
            'values': [row_data]
        }
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            body=body
        ).execute()

        logger.info(f"Cellules mises à jour : {result.get('updates').get('updatedCells')}")  # Log du résultat de l'insertion

        return jsonify({'status': 'success', 'updated_cells': result.get('updates').get('updatedCells')})

    except HttpError as error:
        logger.error(f"Erreur HTTP lors de l'accès au Google Sheets : {error}")  # Log de l'erreur
        return jsonify({'status': 'error', 'message': str(error)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8002))  # Port dynamique pour Qoddi
    app.run(host='0.0.0.0', port=port)