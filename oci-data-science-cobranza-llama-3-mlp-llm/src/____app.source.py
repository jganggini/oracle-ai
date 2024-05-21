import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()

# Generar datos ficticios
num_clients = 10000
data = {
    'client_id': [fake.unique.random_int(min=1000, max=99999) for _ in range(num_clients)],
    'name': [fake.name() for _ in range(num_clients)],
    'email': [fake.email() for _ in range(num_clients)],
    'phone_number': [fake.phone_number() for _ in range(num_clients)],
    'age': [fake.random_int(min=18, max=80) for _ in range(num_clients)],
    'income': [fake.random_int(min=20000, max=100000) for _ in range(num_clients)],
    'payment_history': [fake.random.choice(['on_time', 'late', 'defaulted']) for _ in range(num_clients)],
    'amount_owed': [fake.random_int(min=0, max=20000) for _ in range(num_clients)],
    'communication_preference': [fake.random.choice(['email', 'sms', 'whatsapp', 'app_notification']) for _ in range(num_clients)],
    'last_payment_date': [fake.date_this_year().replace(day=fake.random.choice([10, 25])) for _ in range(num_clients)]
}

df = pd.DataFrame(data)

# Guardar los datos en un archivo CSV
df.to_csv('____source.customers.csv', index=False)