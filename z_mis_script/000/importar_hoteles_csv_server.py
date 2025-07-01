import os
import sys
import django
import psycopg2
from psycopg2.extras import execute_values
import csv

# === Configurar entorno Django ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '../../'))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from apps.backoffice.models import Proveedor

# === Datos del proveedor DISTALCU ===
proveedor_data = {
    'nombre': 'DISTALCU',
    'correo1': 'm.rombaldoni@datagest.it',
    'correo2': 'support@1way2italy.i',
    'correo3': 'm.rombaldoni@datagest.it',
    'telefono': '54266480',
    'detalles_cuenta_bancaria': None,
    'direccion': 'https://www.distalcaribe.com/es/home',
    'tipo': 'hoteles',
    'fee_adultos': 6,
    'fee_ninos': 3,
    'fee_noche': None,
}

proveedor, creado = Proveedor.objects.get_or_create(
    nombre=proveedor_data['nombre'],
    defaults=proveedor_data
)

if creado:
    print(f"✅ Proveedor '{proveedor.nombre}' creado.")
else:
    print(f"ℹ️ Proveedor '{proveedor.nombre}' ya existía. No se creó uno nuevo.")

# === Importar hoteles desde CSV como antes ===
HOTEL_CSV = os.path.join(SCRIPT_DIR, 'HotelImportado.csv')

DB_CONFIG = {
    'dbname': 'db_build',
    'user': 'newneo20',
    'password': '0123456789',
    'host': 'store.prod.travel-sys.loc',
    'port': '5432',
    'sslmode': 'require'
}

CAMPOS = [
    'destino',
    'city_code',
    'hotel_code',
    'hotel_name',
    'hotel_city_code',
    'area_id',
    'giata_id',
    'country_iso_code',
    'country_name',
    'address',
    'email',
    'latitude',
    'longitude',
    'rating',
]

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    with open(HOTEL_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            rows.append([row.get(campo, None) or None for campo in CAMPOS])

    if rows:
        query = f"""
            INSERT INTO backoffice_hotelimportado ({', '.join(CAMPOS)})
            VALUES %s
            ON CONFLICT (hotel_code) DO NOTHING
        """
        execute_values(cursor, query, rows)
        conn.commit()
        print(f"✅ Hoteles procesados: {len(rows)} (nuevos o ignorados por duplicado).")
    else:
        print("⚠️ El archivo HotelImportado.csv no contiene datos.")

except Exception as e:
    print("❌ Error al insertar hoteles:", e)
finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()
