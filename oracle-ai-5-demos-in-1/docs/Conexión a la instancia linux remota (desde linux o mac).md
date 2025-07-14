Es necesario cambiar los permisos del archivo que contiene la key privada descargada previamente en la creación de la instancia. El nombre de la key descargada sigue el formato *ssh-key-YYYY-MM-DD.key.*

Reemplace *ssh-key-0000-00-00.key* por el nombre de su key
```bash
chmod 600 ssh-key-0000-00-00.key
```


Reemplace *ssh-key-0000-00-00.key* por el nombre de su key y 1.1.1.1 por la ip pública de su instancia

```bash
ssh -i ssh-key-0000-00-00.key opc@1.1.1.1
```

La conexión es exitosa si la terminal muestra un prompt parecido al siguiente

```
[opc@…]
```

Para algunas instalaciones, puede que sea necesario ejecutar los comandos en modo administrador, cambie el usuario al usuario administrador usando el siguiente comando

```bash
sudo su
```

Podrá ver que el prompt de la terminal cambia de 

[root@…]

Para volver al usuario opc ejecute
```bash
sudo su opc
```
