# Agora define as variáveis de conexão
DB_HOST = "localhost"    
# DB_PORT = 10425  
DB_USER = "root" 
DB_PASSWORD = "Josias12"
DB_NAME = "nfs"

import os

# Altere para um caminho absoluto para garantir que estamos escrevendo no local correto
DATA_DIR = os.path.join(os.getcwd(), 'data')
