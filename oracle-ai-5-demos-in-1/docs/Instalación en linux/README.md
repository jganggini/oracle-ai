# Despliegue en Oracle Linux

![linux](./images/tux.png)

Este documento describe los pasos necesarios para instalar y configurar el proyecto `Oracle AI 5 Demos en 1` disponible en [GitHub](https://github.com/jganggini/oracle-ai/tree/main/oracle-ai-5-demos-in-1) en Oracle Linux. 

Para la instalación de la demo es necesario realizar los siguientes pasos:

## Creación de una cuenta

Dentro de la demo se utilizarán varios servicios de Oracle, por lo que es necesario crear una cuenta en Oracle Cloud. Si no tiene una cuenta, regístrese en [Oracle Cloud](https://www.oracle.com/cloud/).

[![Watch the video](./images/Crear%20la%20cuenta%20en%20Oracle.png)](https://youtu.be/Kj1Rd52-6cY?list=PLMUWTQHw13gbqqVHaCid3gUBIlvfVKaBu&t=279)

## Despliegue de servicios

Una vez creada la cuenta, es necesario realizar el despliegue de los siguientes servicios:

- Oracle Autonomous Database
- Buckets

Y garantizar el acceso a los siguientes servicios:

- OCI Document Understanding
- OCI Speech
- OCI Generative AI

El paso a paso que describe el despliegue de los servicios está disponible en el siguiente tutorial. En el minuto 4:39 se realiza la instalación con Windows, sin embargo, es posible seleccionar Oracle Linux.

[![Watch the video](./images/Creación%20y%20preparación%20de%20servicios.png)](https://youtu.be/Kj1Rd52-6cY?list=PLMUWTQHw13gbqqVHaCid3gUBIlvfVKaBu&t=279)

> ❗ Si se selecciona Oracle Linux, es importante descargar la key ssh para poder conectarnos luego. Asegúrese de descargar las keys en el paso 3: Networking.

![image](./images/Add%20SSH%20keys.png)

Se descargará un archivo con el formato ssh-key-0000-00-00.key. Esto nos permitirá conectarnos a la instancia en el siguiente paso.

## Conexión a la instancia

La siguiente documentación describe cómo realizar la conexión a un sistema **Oracle Linux 7**.

Cuando la instancia creada se encuentre en estado running, podemos realizar la conexión siguiendo el siguiente tutorial.

[Conexión a la instancia linux remota (desde linux o mac)](./Conexión%20a%20la%20instancia%20linux%20remota%20(desde%20linux%20o%20mac).md)

## Instalación de la demo

Cuando hayamos accedido a la instancia linux es posible realizar la instalación de la demo.
A continuación se describe el paso a paso para realizar la instalación de la demo en un sistema operativo **Oracle Linux 7**.

[Instalación de la demo en Oracle Linux](./Instalación%20de%20la%20demo%20en%20Oracle%20Linux.md)

