# Instalación de la demo en Oracle Linux

## Instalaciones

El primer paso es ejecutar el siguiente comando, realizaremos varias instalaciones y es necesario asegurarnos que el cache está completamente actualizado con toda la metadata.

```bash
yum makecache
```

Vamos a cambiar a usuario administrador mientras instalamos algunos paquetes

```bash
sudo su
```

```bash
yum install git vim python3 python3-pip python3-devel alsa-lib-devel -y
```

### Instalación de la consola de oracle

```bash
dnf -y install oraclelinux-developer-release-el9
dnf -y install python39-oci-cli
```

Ahora podemos volver al usuario opc

```bash
sudo su opc
```

### Instalación de conda

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

```bash
chmod +x Miniconda3-latest-Linux-x86_64.sh
```

```bash
./Miniconda3-latest-Linux-x86_64.sh -b
```

```bash
export PATH=$PATH:/home/opc/miniconda3/bin/
```

```bash
echo 'export PATH=$PATH:/home/opc/miniconda3/bin/' >> ~/.bashrc && source ~/.bashrc
```

### Descarga del repositorio github

```bash
git clone https://github.com/jganggini/oracle-ai.git
```

```bash
cd oracle-ai/oracle-ai-5-demos-in-1/
```

```bash
pip3 install oci python-dotenv oracledb
```

## Autenticación

### Autenticación mediante la cli, creación de API keys y creación del config

Para autenticarnos, ejecutaremos

```bash
oci session authenticate --no-browser
```

Seleccionamos nuestra región y especificamos que vamos a crear un archivo de configuración nuevo y que no vamos a utilizar un navegador

```bash
Do you want to create a new config file? [Y/n]: Y
```

```bash
Do you want to create your config file by logging in through a browser? [Y/n]: n
```

Se nos preguntará por la ubicación del archivo de configuración, podemos dejar el default

```bash
Enter a location for your config [/home/opc/.oci/config]:
```

Se nos preguntará por nuestro Id de usuario y Id de tenancy, aquí podemos proceder a insertar los ids que anotamos previamente

```bash
Enter a user OCID: ocid1.user.oc1........
```

```bash
Enter a tenancy OCID: ocid1.tenancy.oc1..aaaaaaaaoi6b5sxlv4z773boczybqz3h2vspvvru42jysvizl77lky22ijaq
```

Aquí seleccionamos la región

```bash
Enter a region by index or name(e.g.
1: af-johannesburg-1, 2: ap-chiyoda-1, 3: ap-chuncheon-1, 4: ap-chuncheon-2, 5: ap-dcc-canberra-1,
6: ap-dcc-gazipur-1, 7: ap-hyderabad-1, 8: ap-ibaraki-1, 9: ap-melbourne-1, 10: ap-mumbai-1,
11: ap-osaka-1, 12: ap-seoul-1, 13: ap-seoul-2, 14: ap-singapore-1, 15: ap-singapore-2,
16: ap-suwon-1, 17: ap-sydney-1, 18: ap-tokyo-1, 19: ca-montreal-1, 20: ca-toronto-1,
21: eu-amsterdam-1, 22: eu-crissier-1, 23: eu-dcc-dublin-1, 24: eu-dcc-dublin-2, 25: eu-dcc-milan-1,
26: eu-dcc-milan-2, 27: eu-dcc-rating-1, 28: eu-dcc-rating-2, 29: eu-dcc-zurich-1, 30: eu-frankfurt-1,
31: eu-frankfurt-2, 32: eu-jovanovac-1, 33: eu-madrid-1, 34: eu-madrid-2, 35: eu-marseille-1,
36: eu-milan-1, 37: eu-paris-1, 38: eu-stockholm-1, 39: eu-zurich-1, 40: il-jerusalem-1,
41: me-abudhabi-1, 42: me-abudhabi-2, 43: me-abudhabi-3, 44: me-abudhabi-4, 45: me-alain-1,
46: me-dcc-doha-1, 47: me-dcc-muscat-1, 48: me-dubai-1, 49: me-jeddah-1, 50: me-riyadh-1,
51: mx-monterrey-1, 52: mx-queretaro-1, 53: sa-bogota-1, 54: sa-santiago-1, 55: sa-saopaulo-1,
56: sa-valparaiso-1, 57: sa-vinhedo-1, 58: uk-cardiff-1, 59: uk-gov-cardiff-1, 60: uk-gov-london-1,
61: uk-london-1, 62: us-ashburn-1, 63: us-ashburn-2, 64: us-chicago-1, 65: us-gov-ashburn-1,
66: us-gov-chicago-1, 67: us-gov-phoenix-1, 68: us-langley-1, 69: us-luke-1, 70: us-phoenix-1,
71: us-saltlake-2, 72: us-sanjose-1, 73: us-somerset-1, 74: us-thames-1): 64
```

Ahora nos preguntará si queremos generar un API Key, esta key es necesaria para las autenticaciones que se realizarán más adelante, este paso generará una key privada en la ubicación que indiquemos.

```bash
Do you want to generate a new API Signing RSA key pair? (If you decline you will be asked to supply the path to an existing key.) [Y/n]: Y
```

Podemos dejar la ubicación recomendada como default presionando enter ↵. Los siguientes campos se pueden dejar como default presionando ↵.

```bash
Enter a directory for your keys to be created [/home/opc/.oci]:
```

```bash
Enter a name for your key [oci_api_key]:
```

```bash
Public key written to: /home/opc/.oci/oci_api_key_public.pem
```

Aquí debemos tipear tal cual `N/A`

```bash
Enter a passphrase for your private key ("N/A" for no passphrase):
```

Y repetir `N/A`

```bash
Repeat for confirmation:
```

Los pasos anteriores habrán generado un archivo en 

```bash
[DEFAULT]
user=ocid1.user...
fingerprint=00:11:...
tenancy=ocid1.tenancy...
region=us-chicago-1
key_file=/home/opc/.oci/key.pem
```

Una vez se haya generado la configuración y la key, es necesario pegar la key pública generada en la consola, para esto desde el navegador nuestra máquina local podemos ir a 

![image.png](./images/image.png)

![image.png](./images/image%201.png)

![image.png](./images/image%202.png)

### Verificar la autenticación

Para verificar la autenticación podemos ejecutar el comando

```bash
oci iam region list
```

Y deberíamos obtener la siguiente respuesta

![image.png](./images/oci%20iam.png)

### Generación del wallet

Oracle Wallet is a container that stores authentication and signing credentials.

Trusted certificates are stored in the Oracle Wallet when the wallet is used for security credentials.

Es necesario generar un wallet, para lo cual vamos a usar el siguiente comando, en donde debemos

- reemplazar ocid1.autonomousdatabase.oc1... por el id de nuestra base de datos
- reemplazar OraclE3OraclE3. por una contraseña segura

```bash
oci db autonomous-database generate-wallet --autonomous-database-id ocid1.autonomousdatabase.oc1... --password OraclE3OraclE3. --file /home/opc/oracle-ai/oracle-ai-5-demos-in-1/app/wallet/wallet.zip
```

Una vez generado el zip, podemos ir a la ruta de la wallet 

```bash
cd /home/opc/oracle-ai/oracle-ai-5-demos-in-1/app/wallet
```

y descomprimir el archivo

```bash
unzip wallet.zip
```

## Configuración de las variables para la demo

Ahora es necesario editar el archivo .env para especificar las rutas y credenciales de los servicios creados. El archivo puede ser editado usando nuestro editor de texto favorito

```bash
vim /home/opc/oracle-ai/oracle-ai-5-demos-in-1/app/.env
```

```bash
nano /home/opc/oracle-ai/oracle-ai-5-demos-in-1/app/.env
```

## Configuración de la demo

Una vez especificadas las variables, es momento de ejecutar el setup que realizará la instalación de la demo.

```bash
cd setup
```

```bash
python3 setup.py
```

## Configuración de la red

### Apertura de puertos

Ahora ya es posible ejecutar *streamlit*, pero para tener acceso a la app desde nuestra máquina local o desde cualquier otra máquina, es necesario ejecutar

```bash
sudo firewall-cmd --add-port=5901/tcp --permanent
sudo firewall-cmd --reload
```

## Ejecución de la demo

Y listo, ahora podemos ejecutar streamlit.

```bash
streamlit run app.py --server.port 8501 --logger.level=INFO
```