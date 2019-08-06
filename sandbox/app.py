from flask import Flask
import pickle
import os.path
from httplib2 import Http
from apiclient import discovery
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from oauth2client import client
from oauth2client import file
from oauth2client import tools
from apiclient import discovery
from flask import request, jsonify, make_response
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']

app = Flask(__name__)

######################################################
################# API - END POINTS ###################
######################################################

#Aqui simplemente resolvemos si la API se encuentra logueada en Google Drive.
@app.route('/', methods=['GET'])
def index():
    creds = get_credentials()

    if creds:
        data = {'authenticated':True}
        return make_response(jsonify(data), 200)
    else:
        data = {'authenticated':false}
        return make_response(jsonify(data), 200)

#En este endpoint vamos a crear buscar en un DOC la palabra enviada por Query String.
#Se recibe por URL el ID del DOC; si esta no devuelve ningun DOC valido se informa error.
#Si no viene el dato por QS se informa error.
#Se informa si se encuentra o no la palabra.
@app.route('/search-in-doc/<id>', methods=['GET'])
def search_in_doc(id):
    #Palabra que voy a buscar.
    word = request.args.get('word')

    #El dato que viene por QS es obligatorio. Si no esta devolvemos error 500.
    if not word:
        data = {'success':False, "message": "word is undefined"}
        return make_response(jsonify(data), 500)

    #Obtenemos las credenciales.
    credentials = get_credentials()
    http = credentials.authorize(Http())

    DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
    docs_service = discovery.build('docs', 'v1', http=http, discoveryServiceUrl=DISCOVERY_DOC)

    try:
      doc = docs_service.documents().get(documentId=id).execute()
    except:
      doc = None

    #Si no existe el doc que busque por ID directamente arrojo 404.
    if not doc:
        data = {'success':False, "message": "doc does not exist"}
        return make_response(jsonify(data), 404)

    #Resolvemos el contenido del documento encontrado.
    doc_content = doc.get('body').get('content')
    contenido = (read_strucutural_elements(doc_content))

    #Buscamos la palabra enviada por Query String en el documento. Si esta devolvemos 200, si no 404.
    if (contenido.find(word) != -1):
        data = {'success':True}
        return make_response(jsonify(data), 200)
    else:
        data = {'success':False}
        return make_response(jsonify(data), 404)

#En este endpoint vamos a crear un DOC segun los datos enviados.
# Ejemplo:
#   Request:
#     POST /file
#     {"titulo":"Pagos a prov", "descripcion":"Tengo que hacer un pago"}

# Primero crearemos el DOC. Si esta todo bien enviaremos el contenido del mismo.
@app.route('/file', methods=['POST'])
def create_file():
    if not request.get_json():
        data = {'success':False, "message": "bad parameters"}
        return make_response(jsonify(data), 404)

    data = request.get_json()

    if not data.has_key("titulo"):
        data = {'success':False, "message": "bad parameters, 'titulo' is missing."}
        return make_response(jsonify(data), 404)

    if not data.has_key("descripcion"):
        data = {'success':False, "message": "bad parameters, 'descripcion' is missing."}
        return make_response(jsonify(data), 404)

    #Data para crear el documento
    body = {
      'title': data["titulo"]
    }

    #Obtenemos las credenciales.
    creds = check_login()
    service = build('docs', 'v1', credentials=creds)

    #Creamos el doc
    doc = service.documents().create(body=body).execute()

    if not doc:
        data = {'success':False, "message": "can not create the doc."}
        return make_response(jsonify(data), 500)

    #Data del contenido del doc.
    DOCUMENT_ID = doc.get("documentId")
    requests = [
         {
            'insertText': {
                'location': {
                    'index':1,
                },
                'text': data["descripcion"]
            }
        }
    ]
    result = service.documents().batchUpdate(documentId=DOCUMENT_ID, body={'requests': requests}).execute()

    if not result:
        data = {'success':False, "message": "can not create the doc."}
        return make_response(jsonify(data), 500)

    data = {'id':DOCUMENT_ID, "titulo": data["titulo"], "descripcion": data["descripcion"]}

    print(data)
    return make_response(jsonify(data), 200)



######################################################
#################### Funciones #######################
######################################################

#Check del login. Para volver a logear borrar token.pickle.
def check_login():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

#Trae las credenciales necesarias para hablar con la API de Google Drive.
def get_credentials():
  check_login()

  try:
    store = file.Storage('token.json')
    credentials = store.get()
  except:
    store = None
    credentials = None

  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    credentials = tools.run_flow(flow, store)

  return credentials

#Leemos el contenido de un elemento del archivo.
def read_paragraph_element(element):
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')

#Leemos el contenido del archivo.
def read_strucutural_elements(elements):
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_strucutural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_strucutural_elements(toc.get('content'))
    return text


#Para poder correr con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')